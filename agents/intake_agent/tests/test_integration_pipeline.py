"""
Integration Tests for Complete Processing Pipeline

Tests the full flow:
1. Input validation (applicant data)
2. Canonical output assembly (deterministic)
3. Evidence linking (traceability)
4. LOS schema validation (strict)
5. Callback delivery (success/failure/partial)

End-to-end scenarios test the contract between domain layers.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.domain.output.canonical_builder import assemble_canonical_output
from src.domain.output.evidence.evidence_linker import link_evidence_to_output
from src.domain.output.schema_validator import validate_los_output, LOSSchemaValidationError
from src.domain.callbacks.callback_models import (
    SuccessCallback,
    FailureCallback,
    PartialSuccessCallback,
    ErrorDetail,
    SectionStatus,
)
from src.services.callback_service import CallbackService
from src.adapters.callbacks.callback_adapter import CallbackHTTPAdapter
from src.repositories.evidence_repository import InMemoryEvidenceRepository


class TestIntegrationSuccessPath:
    """Integration tests for successful application processing."""

    @pytest.mark.asyncio
    async def test_complete_success_flow(self):
        """
        Full pipeline: input → canonical output → evidence linking → 
        validation → success callback.
        """
        # Setup
        mock_adapter = AsyncMock(spec=CallbackHTTPAdapter)
        mock_adapter.send_async.return_value = {"status": "sent", "timestamp": "2026-02-11T10:30:00Z"}
        service = CallbackService(adapter=mock_adapter)
        repo = InMemoryEvidenceRepository()

        # Step 1: Input data (LOS schema compliant)
        applicants = [
            {
                "applicant_id": "APPL-001",
                "applicant_role": "PRIMARY",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone_number": "+1-555-0100",
            }
        ]

        # Step 2: Assemble canonical output
        canonical_output = assemble_canonical_output(
            application={
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
            },
            applicants=applicants,
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-11T10:30:00Z",
        )

        assert "applicants" in canonical_output
        assert len(canonical_output["applicants"]) == 1

        # Step 3: Validate schema (before evidence linking - IMPORTANT)
        validate_los_output(canonical_output)  # Raises if invalid

        # Step 4: Store and link evidence
        await repo.store_evidence_path(
            application_id="APP-001",
            evidence_id="EV-001",
            evidence_type="validation",
            path="/validations/email_check.json",
            source="email_validator",
            entity_type="applicant",
            entity_id="APPL-001",
            rule_id="EMAIL_FORMAT",
        )

        # Step 5: Link evidence to validated output
        from src.domain.output.evidence.evidence_models import EvidenceReference
        evidence_ref = EvidenceReference(
            id="EV-001",
            type="validation",
            source="email_validator",
            path="/validations/email_check.json",
            created_at="2026-02-11T10:30:00Z",
        )
        linked_output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=[evidence_ref],
        )

        assert "evidence" in linked_output
        assert len(linked_output["evidence"]) == 1

        # Step 6: Send success callback (uses canonical output, NOT linked output)
        success_callback = SuccessCallback(
            application_id="APP-001",
            canonical_output=canonical_output,
            timestamp="2026-02-11T10:30:00Z",
        )

        response = await service.send_success_callback(
            callback_url="https://los-system.example.com/callback",
            success_callback=success_callback,
        )

        # Verify
        assert response["status"] == "sent"
        assert mock_adapter.send_async.called

        # Verify evidence was stored
        evidence = await repo.get_evidence_by_application("APP-001")
        assert len(evidence) == 1
        assert evidence[0]["id"] == "EV-001"

    @pytest.mark.asyncio
    async def test_deterministic_output_multiple_calls(self):
        """Same input should produce identical canonical output."""
        applicants = [
            {"id": "APPL-001", "name": "John Doe"},
            {"id": "APPL-002", "name": "Jane Smith"},
        ]

        output1 = assemble_canonical_output(applicants=applicants, generated_at="2026-02-11T10:30:00Z")
        output2 = assemble_canonical_output(applicants=applicants, generated_at="2026-02-11T10:30:00Z")

        # Same JSON structure (deterministic key ordering)
        import json
        assert json.dumps(output1, sort_keys=True) == json.dumps(output2, sort_keys=True)

    def test_schema_validation_catches_invalid_output(self):
        """Schema validation should reject invalid outputs."""
        invalid_output = {
            "applicants": [
                {"id": "APPL-001", "name": "John"}
            ],
            "invalid_field": "should not be here",
        }

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(invalid_output)


class TestIntegrationFailurePath:
    """Integration tests for application processing failures."""

    @pytest.mark.asyncio
    async def test_validation_error_failure_callback(self):
        """When validation fails, send failure callback."""
        mock_adapter = AsyncMock(spec=CallbackHTTPAdapter)
        mock_adapter.send_async.return_value = {"status": "sent"}
        service = CallbackService(adapter=mock_adapter)

        # Invalid data
        invalid_output = {
            "applicants": [],
            "invalid_extra_field": "not allowed",
        }

        # Try to validate
        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(invalid_output)

        # Create failure callback for the error
        failure_callback = FailureCallback(
            application_id="APP-001",
            error_code="SCHEMA_VALIDATION_FAILED",
            error_message=str(exc_info.value),
            errors=[
                ErrorDetail(
                    field="root",
                    code="EXTRA_FORBID",
                    message="Extra fields not allowed: invalid_extra_field",
                )
            ],
            timestamp="2026-02-11T10:30:00Z",
        )

        # Send failure callback
        response = await service.send_failure_callback(
            callback_url="https://los-system.example.com/failure",
            failure_callback=failure_callback,
        )

        assert response["status"] == "sent"
        mock_adapter.send_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_accumulation_in_failure_callback(self):
        """Multiple errors should accumulate in failure callback."""
        errors = [
            ErrorDetail(
                field="applicants.0.email",
                code="INVALID_EMAIL",
                message="Email format is invalid",
            ),
            ErrorDetail(
                field="applicants.0.phone",
                code="INVALID_PHONE",
                message="Phone format is invalid",
            ),
            ErrorDetail(
                field="applicants.1.income",
                code="INVALID_INCOME",
                message="Income must be a non-negative number",
            ),
        ]

        failure_callback = FailureCallback(
            application_id="APP-001",
            error_code="MULTIPLE_VALIDATION_ERRORS",
            error_message="3 validation errors detected",
            errors=errors,
            timestamp="2026-02-11T10:30:00Z",
        )

        callback_dict = failure_callback.to_dict()

        assert len(callback_dict["errors"]) == 3
        assert callback_dict["errors"][0]["field"] == "applicants.0.email"
        assert callback_dict["errors"][2]["field"] == "applicants.1.income"


class TestIntegrationPartialSuccessPath:
    """Integration tests for partial success scenarios."""

    @pytest.mark.asyncio
    async def test_enrichment_failure_partial_success(self):
        """When some enrichment fails, send partial success callback."""
        mock_adapter = AsyncMock(spec=CallbackHTTPAdapter)
        mock_adapter.send_async.return_value = {"status": "sent"}
        service = CallbackService(adapter=mock_adapter)

        # Canonical output (core processing succeeded)
        from src.domain.output.canonical_builder import assemble_canonical_output
        
        canonical_output = assemble_canonical_output(
            application={
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
            },
            applicants=[
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                }
            ],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-11T10:30:00Z",
        )

        # Validate schema BEFORE processing
        validate_los_output(canonical_output)  # Raises if invalid

        sections = [
            SectionStatus(
                section_name="applicant_extraction",
                status="SUCCESS",
            ),
            SectionStatus(
                section_name="credit_enrichment",
                status="FAILURE",
                error_message="Credit check service unavailable (HTTP 503)",
            ),
            SectionStatus(
                section_name="employment_verification",
                status="SUCCESS",
            ),
        ]

        partial_callback = PartialSuccessCallback(
            application_id="APP-001",
            sections=sections,
            canonical_output=canonical_output,
            timestamp="2026-02-11T10:30:00Z",
        )

        response = await service.send_partial_success_callback(
            callback_url="https://los-system.example.com/partial",
            partial_callback=partial_callback,
        )

        assert response["status"] == "sent"

        # Verify payload structure
        callback_dict = partial_callback.to_dict()
        assert callback_dict["status"] == "PARTIAL_SUCCESS"
        assert len(callback_dict["sections"]) == 3
        assert callback_dict["sections"][1]["status"] == "FAILURE"
        assert "Credit check service" in callback_dict["sections"][1]["error_message"]

    @pytest.mark.asyncio
    async def test_section_status_filtering(self):
        """Can filter sections by status in partial success."""
        sections = [
            SectionStatus(section_name="section_a", status="SUCCESS"),
            SectionStatus(section_name="section_b", status="FAILURE", error_message="Error B"),
            SectionStatus(section_name="section_c", status="SUCCESS"),
            SectionStatus(section_name="section_d", status="FAILURE", error_message="Error D"),
        ]

        partial_callback = PartialSuccessCallback(
            application_id="APP-001",
            sections=sections,
            timestamp="2026-02-11T10:30:00Z",
        )

        callback_dict = partial_callback.to_dict()

        # Can filter sections on receiving end
        failed_sections = [
            s for s in callback_dict["sections"] if s["status"] == "FAILURE"
        ]
        successful_sections = [
            s for s in callback_dict["sections"] if s["status"] == "SUCCESS"
        ]

        assert len(failed_sections) == 2
        assert len(successful_sections) == 2


class TestIntegrationImmutability:
    """Test that immutability contracts are maintained across layers."""

    def test_canonical_output_immutability_of_inputs(self):
        """Modifying input should not affect assembled output."""
        applicants = [
            {"id": "APPL-001", "name": "John Doe"},
        ]

        # Assemble
        output = assemble_canonical_output(applicants=applicants, generated_at="2026-02-11T10:30:00Z")

        # Modify original
        applicants[0]["name"] = "Jane Doe"

        # Output should be unchanged
        assert output["applicants"][0]["name"] == "John Doe"

    def test_evidence_linking_immutability(self):
        """Evidence linking should not mutate original output."""
        from src.domain.output.evidence.evidence_models import EvidenceReference
        
        output = {
            "applicants": [{"id": "APPL-001", "name": "John"}],
            "metadata": {},
        }

        evidence_ref = EvidenceReference(
            id="EV-001",
            type="validation",
            source="validator",
            path="/path.json",
            created_at="2026-02-11T10:30:00Z",
        )
        
        linked = link_evidence_to_output(
            canonical_output=output,
            evidence_refs=[evidence_ref],
        )

        # Original should not have evidence
        assert "evidence" not in output
        # Linked version should have it
        assert "evidence" in linked

    def test_callback_models_immutable(self):
        """Callback models should be immutable after creation."""
        callback = SuccessCallback(
            application_id="APP-001",
            canonical_output={},
            timestamp="2026-02-11T10:30:00Z",
        )

        with pytest.raises(AttributeError):
            callback.application_id = "APP-002"

        with pytest.raises(AttributeError):
            callback.timestamp = "2026-02-12T10:30:00Z"


class TestIntegrationErrorPropagation:
    """Test that errors propagate correctly through layers."""

    def test_schema_validation_error_has_details(self):
        """Schema validation error should include enough details for callback."""
        invalid_output = {
            "applicants": "not a list",  # Should be list
        }

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(invalid_output)

        error = exc_info.value
        error_str = str(error)

        # Error message should be usable in failure callback
        assert len(error_str) > 0
        assert "applicants" in error_str.lower() or "input should be a valid" in error_str.lower()

    @pytest.mark.asyncio
    async def test_adapter_error_propagates(self):
        """Adapter errors should propagate through service."""
        from src.adapters.callbacks.callback_adapter import CallbackSendError

        mock_adapter = AsyncMock(spec=CallbackHTTPAdapter)
        mock_adapter.send_async.side_effect = CallbackSendError(
            message="Connection failed",
            url="https://example.com",
            status_code=500,
        )

        service = CallbackService(adapter=mock_adapter)

        callback = SuccessCallback(
            application_id="APP-001",
            canonical_output={},
            timestamp="2026-02-11T10:30:00Z",
        )

        with pytest.raises(CallbackSendError):
            await service.send_success_callback(
                callback_url="https://example.com",
                success_callback=callback,
            )


class TestIntegrationEvidenceFlow:
    """Test evidence storage and linking in full context."""

    @pytest.mark.asyncio
    async def test_evidence_lifecycle(self):
        """Test storing, retrieving, and deleting evidence."""
        repo = InMemoryEvidenceRepository()

        # Store evidence for applicant
        await repo.store_evidence_path(
            application_id="APP-001",
            evidence_id="EV-001",
            evidence_type="document",
            path="/documents/passport.pdf",
            source="document_scanner",
            entity_type="applicant",
            entity_id="APPL-001",
            rule_id="PASSPORT_VERIFICATION",
        )

        await repo.store_evidence_path(
            application_id="APP-001",
            evidence_id="EV-002",
            evidence_type="validation",
            path="/validations/income.json",
            source="income_validator",
            entity_type="applicant",
            entity_id="APPL-001",
            rule_id="INCOME_VERIFICATION",
        )

        # Retrieve all evidence for application
        evidence = await repo.get_evidence_by_application("APP-001")
        assert len(evidence) == 2

        # Retrieve specific evidence
        ev001 = await repo.get_evidence_by_id("EV-001")
        assert ev001["type"] == "document"  # Repository returns "type", not "evidence_type"

        # Link evidence to output
        from src.domain.output.evidence.evidence_models import EvidenceReference
        
        output = {"applicants": [{"id": "APPL-001"}]}
        evidence_refs = [
            EvidenceReference(
                id="EV-001",
                type="document",
                source="document_scanner",
                path="/documents/passport.pdf",
                created_at="2026-02-11T10:30:00Z",
            ),
            EvidenceReference(
                id="EV-002",
                type="validation",
                source="income_validator",
                path="/validations/income.json",
                created_at="2026-02-11T10:30:00Z",
            ),
        ]
        linked_output = link_evidence_to_output(
            canonical_output=output,
            evidence_refs=evidence_refs,
        )

        assert len(linked_output["evidence"]) == 2

        # Delete evidence
        deleted = await repo.delete_evidence("EV-001")
        assert deleted is True

        # Verify deletion
        remaining = await repo.get_evidence_by_application("APP-001")
        assert len(remaining) == 1
        assert remaining[0]["id"] == "EV-002"
