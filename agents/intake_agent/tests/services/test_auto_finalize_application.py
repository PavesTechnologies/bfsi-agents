import pytest
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.services.intake_services.loan_intake_service import LoanIntakeService
from src.models.models import LoanApplication, Applicant


class _FakeEvidenceRepo:
    def __init__(self, records):
        self._records = records

    async def get_evidence_by_application(self, application_id: str):
        return list(self._records.get(application_id, []))


@pytest.mark.asyncio
async def test_auto_finalize_application_sets_flag_and_is_idempotent(db_session: AsyncSession, monkeypatch):
    """
    Service-level test to ensure:
    - auto_finalize_application marks application as finalized
    - second invocation is a no-op (idempotent)
    """
    app_id = uuid4()

    # Seed DB with minimal application + one applicant
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

    db_session.add(application)
    db_session.add(applicant)
    await db_session.commit()

    # Fake evidence repository (no evidence required for this test)
    evidence_repo = _FakeEvidenceRepo(records={})

    # Callback client is a simple namespace with async no-op methods
    async def _noop(*_, **__):
        return None

    callback_client = SimpleNamespace(
        send_success_callback=_noop,
        send_partial_success_callback=_noop,
        send_failure_callback=_noop,
    )

    service = LoanIntakeService(callback_client=callback_client)

    # First call should finalize
    await service.auto_finalize_application(
        application_id=app_id,
        db=db_session,
        callback_url="https://example.com/callback",
        evidence_repo=evidence_repo,
        enrichments={},
    )

    refreshed = await db_session.execute(
        select(LoanApplication).where(LoanApplication.application_id == app_id)
    )
    obj = refreshed.scalar_one()
    assert obj.finalized_flag is True

    # Second call should be a no-op (still finalized, no errors)
    await service.auto_finalize_application(
        application_id=app_id,
        db=db_session,
        callback_url="https://example.com/callback",
        evidence_repo=evidence_repo,
        enrichments={},
    )

