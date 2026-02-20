import pytest
from unittest.mock import AsyncMock

from src.services.intake_services.loan_intake_service import LoanIntakeService
from src.adapters.http.callback.callback_client import CallbackDeliveryError
from src.domain.output.schema_validator import LOSSchemaValidationError


def _sample_application():
    return {
        "application_id": "app-123",
        "loan_type": "PERSONAL",
    }


def _sample_applicant():
    return [
        {
            "applicant_id": "a-1",
            "applicant_role": "PRIMARY",
            "first_name": "Jane",
            "last_name": "Doe",
        }
    ]


@pytest.mark.asyncio
async def test_success_flow_calls_success_callback():
    callback_client = AsyncMock()
    callback_client.send_success_callback = AsyncMock()
    callback_client.send_partial_success_callback = AsyncMock()
    callback_client.send_failure_callback = AsyncMock()

    service = LoanIntakeService(callback_client=callback_client)

    result = await service.process_final_output(
        application=_sample_application(),
        applicants=_sample_applicant(),
        enrichments={},
        evidence_refs=[],
        generated_at="2025-01-01T00:00:00Z",
        callback_url="https://example/cb",
    )

    assert result["status"] == "SUCCESS"
    callback_client.send_success_callback.assert_awaited_once()


@pytest.mark.asyncio
async def test_partial_flow_calls_partial_callback():
    callback_client = AsyncMock()
    callback_client.send_success_callback = AsyncMock()
    callback_client.send_partial_success_callback = AsyncMock()
    callback_client.send_failure_callback = AsyncMock()

    service = LoanIntakeService(callback_client=callback_client)

    result = await service.process_final_output(
        application=_sample_application(),
        applicants=_sample_applicant(),
        enrichments={},
        evidence_refs=[],
        generated_at="2025-01-01T00:00:00Z",
        callback_url="https://example/cb",
        validation_warnings=["minor formatting issue"],
    )

    assert result["status"] == "PARTIAL_SUCCESS"
    callback_client.send_partial_success_callback.assert_awaited_once()


@pytest.mark.asyncio
async def test_schema_failure_calls_failure_callback(monkeypatch):
    # Monkeypatch validator to raise LOSSchemaValidationError
    def _raise_validator(_):
        raise LOSSchemaValidationError("invalid")

    monkeypatch.setattr(
        "src.services.intake_services.loan_intake_service.validate_los_output", _raise_validator
    )

    callback_client = AsyncMock()
    callback_client.send_success_callback = AsyncMock()
    callback_client.send_partial_success_callback = AsyncMock()
    callback_client.send_failure_callback = AsyncMock()

    service = LoanIntakeService(callback_client=callback_client)

    result = await service.process_final_output(
        application=_sample_application(),
        applicants=_sample_applicant(),
        enrichments={},
        evidence_refs=[],
        generated_at="2025-01-01T00:00:00Z",
        callback_url="https://example/cb",
    )

    assert result["status"] == "FAILURE"
    callback_client.send_failure_callback.assert_awaited_once()


@pytest.mark.asyncio
async def test_callback_delivery_failure_does_not_crash(monkeypatch):
    # Simulate send_success_callback raising CallbackDeliveryError
    async def _raise(*_, **__):
        raise CallbackDeliveryError("network")

    callback_client = AsyncMock()
    callback_client.send_success_callback = AsyncMock(side_effect=_raise)
    callback_client.send_partial_success_callback = AsyncMock()
    callback_client.send_failure_callback = AsyncMock()

    service = LoanIntakeService(callback_client=callback_client)

    # Should not raise despite callback delivery error
    result = await service.process_final_output(
        application=_sample_application(),
        applicants=_sample_applicant(),
        enrichments={},
        evidence_refs=[],
        generated_at="2025-01-01T00:00:00Z",
        callback_url="https://example/cb",
    )

    assert result["status"] == "SUCCESS"
