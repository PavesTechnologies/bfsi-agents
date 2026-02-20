from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import LoanApplication, Applicant, LoanFinalizationEvent
from src.repositories.evidence_repository import InMemoryEvidenceRepository
from src.services.intake_services.loan_intake_service import LoanIntakeService
from src.adapters.http.callback.callback_client import CallbackDeliveryError


class _FakeCallbackClient:
    def __init__(self):
        self.success_calls = []
        self.partial_calls = []
        self.failure_calls = []
        self.raise_on_success = False

    async def send_success_callback(self, url, payload):
        if self.raise_on_success:
            raise CallbackDeliveryError("network error")
        self.success_calls.append((url, payload))

    async def send_partial_success_callback(self, url, payload):
        self.partial_calls.append((url, payload))

    async def send_failure_callback(self, url, payload):
        self.failure_calls.append((url, payload))


async def _seed_minimal_application(session: AsyncSession) -> uuid4:
    app_id = uuid4()
    application = LoanApplication(
        application_id=app_id,
        loan_type="PERSONAL",
    )
    applicant = Applicant(
        application_id=app_id,
        first_name="Jane",
        last_name="Doe",
        date_of_birth=datetime.utcnow().date(),
        applicant_role="PRIMARY",
        email="jane@example.com",
        phone_number="+1-555-0100",
        gender="FEMALE",
    )
    session.add(application)
    session.add(applicant)
    await session.commit()
    return app_id


@pytest.mark.asyncio
async def test_success_flow_persists_event_and_callback_result(db_session: AsyncSession):
    app_id = await _seed_minimal_application(db_session)
    callback_client = _FakeCallbackClient()
    service = LoanIntakeService(callback_client=callback_client)

    repo = InMemoryEvidenceRepository()

    await service.auto_finalize_application(
        application_id=app_id,
        db=db_session,
        callback_url="https://example.com/callback",
        evidence_repo=repo,
        enrichments={},
        enrichment_errors=[],
    )

    result = await db_session.execute(
        select(LoanFinalizationEvent).where(LoanFinalizationEvent.application_id == app_id)
    )
    event = result.scalar_one()

    assert event.status == "SUCCESS"
    assert isinstance(event.response_payload, dict)
    assert event.callback_result is not None
    assert event.callback_result.get("ok") is True


@pytest.mark.asyncio
async def test_partial_success_persists_event(db_session: AsyncSession):
    app_id = await _seed_minimal_application(db_session)
    callback_client = _FakeCallbackClient()
    service = LoanIntakeService(callback_client=callback_client)
    repo = InMemoryEvidenceRepository()

    enrichment_errors = ["phone_verification_failed"]

    await service.auto_finalize_application(
        application_id=app_id,
        db=db_session,
        callback_url="https://example.com/callback",
        evidence_repo=repo,
        enrichments={},
        enrichment_errors=enrichment_errors,
    )

    result = await db_session.execute(
        select(LoanFinalizationEvent).where(LoanFinalizationEvent.application_id == app_id)
    )
    event = result.scalar_one()

    assert event.status == "PARTIAL_SUCCESS"
    assert isinstance(event.response_payload, dict)


@pytest.mark.asyncio
async def test_schema_failure_stores_failure_event(db_session: AsyncSession, monkeypatch):
    app_id = await _seed_minimal_application(db_session)
    callback_client = _FakeCallbackClient()
    service = LoanIntakeService(callback_client=callback_client)
    repo = InMemoryEvidenceRepository()

    # Corrupt schema by monkeypatching validator to always raise
    from src.services.intake_services import loan_intake_service as module_under_test

    def _raise(_):
        from src.domain.output.schema_validator import LOSSchemaValidationError

        raise LOSSchemaValidationError("invalid")

    monkeypatch.setattr(module_under_test, "validate_los_output", _raise)

    await service.auto_finalize_application(
        application_id=app_id,
        db=db_session,
        callback_url="https://example.com/callback",
        evidence_repo=repo,
        enrichments={},
        enrichment_errors=[],
    )

    result = await db_session.execute(
        select(LoanFinalizationEvent).where(LoanFinalizationEvent.application_id == app_id)
    )
    event = result.scalar_one()

    assert event.status == "FAILURE"
    assert isinstance(event.response_payload, dict)


@pytest.mark.asyncio
async def test_callback_failure_event_still_stored(db_session: AsyncSession):
    app_id = await _seed_minimal_application(db_session)
    callback_client = _FakeCallbackClient()
    callback_client.raise_on_success = True

    service = LoanIntakeService(callback_client=callback_client)
    repo = InMemoryEvidenceRepository()

    await service.auto_finalize_application(
        application_id=app_id,
        db=db_session,
        callback_url="https://example.com/callback",
        evidence_repo=repo,
        enrichments={},
        enrichment_errors=[],
    )

    result = await db_session.execute(
        select(LoanFinalizationEvent).where(LoanFinalizationEvent.application_id == app_id)
    )
    event = result.scalar_one()

    # Even though callback failed, event exists and has failure metadata
    assert event.callback_result is not None
    assert event.callback_result.get("ok") is False


@pytest.mark.asyncio
async def test_idempotency_second_call_does_not_create_new_event(db_session: AsyncSession):
    app_id = await _seed_minimal_application(db_session)
    callback_client = _FakeCallbackClient()
    service = LoanIntakeService(callback_client=callback_client)
    repo = InMemoryEvidenceRepository()

    await service.auto_finalize_application(
        application_id=app_id,
        db=db_session,
        callback_url="https://example.com/callback",
        evidence_repo=repo,
        enrichments={},
        enrichment_errors=[],
    )

    # Reset callback records and call again
    callback_client.success_calls.clear()

    await service.auto_finalize_application(
        application_id=app_id,
        db=db_session,
        callback_url="https://example.com/callback",
        evidence_repo=repo,
        enrichments={},
        enrichment_errors=[],
    )

    result = await db_session.execute(
        select(LoanFinalizationEvent).where(LoanFinalizationEvent.application_id == app_id)
    )
    events = result.scalars().all()

    # Only one audit event should exist
    assert len(events) == 1

