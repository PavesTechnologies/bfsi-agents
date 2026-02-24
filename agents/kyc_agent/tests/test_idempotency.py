from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.models.enums import IdempotencyStatus
from src.services.kyc_services.kyc_orchestrator import KYCOrchestratorService


# Mocking the Pydantic request model
class MockAddress:
    line1 = "123 Main St"
    line2 = None
    city = "New York"
    state = "NY"
    zip = "10001"


class MockKYCRequest:
    idempotency_key = "test-key-123"
    applicant_id = "user_1"
    full_name = "John Doe"
    dob = "1990-01-01"
    ssn = "123456789"
    phone = "+1234567890"
    email = "john@example.com"
    address = MockAddress()

    def model_dump(self, mode="json"):
        return {
            "idempotency_key": self.idempotency_key,
            "applicant_id": self.applicant_id,
        }


@pytest.fixture
def service():
    db_session = AsyncMock()
    service = KYCOrchestratorService(db_session)
    service.repo = AsyncMock()
    service.graph = AsyncMock()
    return service


class TestKYCIdempotency:
    @pytest.mark.asyncio
    async def test_first_time_execution_success(self, service):
        """Standard flow: No existing record, should run graph and return result."""
        # Setup
        payload = MockKYCRequest()
        service.repo.get_request_by_idempotency.return_value = None
        service.repo.create_kyc_case.return_value = MagicMock(id="kyc_001")
        service.graph.ainvoke.return_value = {
            "risk_decision": {"final_status": "APPROVED"}
        }

        # Execute
        result = await service.verify_identity(payload)

        # Verify
        assert result["status"] == "APPROVED"
        service.repo.create_kyc_case.assert_called_once()
        service.graph.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_idempotent_retrieval(self, service):
        """Should return cached response if key and hash match."""
        payload = MockKYCRequest()
        cached_response = {"status": "APPROVED", "kyc_result": "MATCH"}
        target_hash = "MATCHING_HASH"

        mock_record = MagicMock()
        mock_record.payload_hash = target_hash
        mock_record.response_status = IdempotencyStatus.SUCCESS
        mock_record.response_payload = cached_response
        service.repo.get_request_by_idempotency.return_value = mock_record

        # FIX: Patch the hash function specifically inside the service module
        with patch(
            "src.services.kyc_services.kyc_orchestrator.generate_payload_hash",
            return_value=target_hash,
        ):
            result = await service.verify_identity(payload)

        assert result == cached_response
        service.graph.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_currently_pending(self, service):
        """Should raise 202 Accepted if a request is already running."""
        payload = MockKYCRequest()
        target_hash = "MATCHING_HASH"

        mock_record = MagicMock()
        mock_record.payload_hash = target_hash
        mock_record.response_status = IdempotencyStatus.PENDING
        mock_record.kyc_id = "kyc_pending_99"
        service.repo.get_request_by_idempotency.return_value = mock_record

        # FIX: Patch the hash function specifically inside the service module
        with patch(
            "src.services.kyc_services.kyc_orchestrator.generate_payload_hash",
            return_value=target_hash,
        ):
            with pytest.raises(HTTPException) as exc:
                await service.verify_identity(payload)

        assert exc.value.status_code == 202

    @pytest.mark.asyncio
    async def test_idempotency_key_collision_different_payload(self, service):
        """Should raise 409 Conflict if same key is used for different data."""
        # Setup
        payload = MockKYCRequest()
        mock_record = MagicMock()
        mock_record.payload_hash = "DIFFERENT_HASH"  # Hash mismatch
        service.repo.get_request_by_idempotency.return_value = mock_record

        # Execute & Verify
        with pytest.raises(HTTPException) as exc:
            await service.verify_identity(payload)

        assert exc.value.status_code == 409
        assert "different payload" in exc.value.detail
