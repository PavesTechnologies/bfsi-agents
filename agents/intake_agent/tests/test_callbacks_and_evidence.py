"""
Tests for Callback Models and Service

Test cases:
- Success callback construction and serialization
- Failure callback with error details
- Partial success callback with section statuses
- Callback service orchestration
- Evidence repository storage and retrieval
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.domain.callbacks import (
    SuccessCallback,
    FailureCallback,
    PartialSuccessCallback,
    ErrorDetail,
    SectionStatus,
    CallbackStatus,
)
from src.adapters.callbacks import CallbackHTTPAdapter, CallbackSendError
from src.repositories.evidence_repository import (
    EvidenceRepository,
    InMemoryEvidenceRepository,
)


class TestSuccessCallback:
    """Test success callback model."""

    def test_success_callback_creation(self):
        """Create success callback with minimal fields."""
        callback = SuccessCallback(
            application_id="APP-001",
            canonical_output={"applicants": []},
            timestamp="2026-02-11T10:30:00Z",
        )

        assert callback.application_id == "APP-001"
        assert callback.status == CallbackStatus.SUCCESS.value
        assert callback.canonical_output == {"applicants": []}

    def test_success_callback_to_dict(self):
        """Success callback should serialize to dict."""
        callback = SuccessCallback(
            application_id="APP-001",
            canonical_output={"applicants": []},
            timestamp="2026-02-11T10:30:00Z",
        )

        callback_dict = callback.to_dict()

        assert callback_dict["application_id"] == "APP-001"
        assert callback_dict["status"] == "SUCCESS"
        assert callback_dict["canonical_output"] == {"applicants": []}
        assert callback_dict["timestamp"] == "2026-02-11T10:30:00Z"

    def test_success_callback_immutable(self):
        """Success callback should be immutable."""
        callback = SuccessCallback(
            application_id="APP-001",
            canonical_output={},
            timestamp="2026-02-11T10:30:00Z",
        )

        with pytest.raises(AttributeError):
            callback.application_id = "APP-002"


class TestFailureCallback:
    """Test failure callback model."""

    def test_failure_callback_minimal(self):
        """Create failure callback with minimal fields."""
        callback = FailureCallback(
            application_id="APP-001",
            error_code="VALIDATION_FAILED",
            error_message="Email validation failed",
            timestamp="2026-02-11T10:30:00Z",
        )

        assert callback.application_id == "APP-001"
        assert callback.status == CallbackStatus.FAILURE.value
        assert callback.error_code == "VALIDATION_FAILED"
        assert callback.error_message == "Email validation failed"

    def test_failure_callback_with_errors(self):
        """Failure callback with detailed errors."""
        errors = [
            ErrorDetail(
                field="email",
                code="INVALID_EMAIL",
                message="Email format is invalid",
            ),
            ErrorDetail(
                field="phone",
                code="INVALID_PHONE",
                message="Phone format is invalid",
            ),
        ]

        callback = FailureCallback(
            application_id="APP-001",
            error_code="VALIDATION_FAILED",
            error_message="Multiple validation errors",
            errors=errors,
            timestamp="2026-02-11T10:30:00Z",
        )

        assert len(callback.errors) == 2
        assert callback.errors[0].field == "email"

    def test_failure_callback_to_dict(self):
        """Failure callback should serialize to dict."""
        errors = [
            ErrorDetail(
                field="email",
                code="INVALID_EMAIL",
                message="Email format is invalid",
            )
        ]

        callback = FailureCallback(
            application_id="APP-001",
            error_code="VALIDATION_FAILED",
            error_message="Validation failed",
            errors=errors,
            timestamp="2026-02-11T10:30:00Z",
        )

        callback_dict = callback.to_dict()

        assert callback_dict["application_id"] == "APP-001"
        assert callback_dict["status"] == "FAILURE"
        assert callback_dict["error_code"] == "VALIDATION_FAILED"
        assert len(callback_dict["errors"]) == 1
        assert callback_dict["errors"][0]["field"] == "email"


class TestPartialSuccessCallback:
    """Test partial success callback model."""

    def test_partial_success_minimum(self):
        """Create partial success callback."""
        sections = [
            SectionStatus(
                section_name="applicants",
                status="SUCCESS",
            ),
            SectionStatus(
                section_name="enrichment",
                status="FAILURE",
                error_message="Credit check failed",
            ),
        ]

        callback = PartialSuccessCallback(
            application_id="APP-001",
            sections=sections,
            timestamp="2026-02-11T10:30:00Z",
        )

        assert callback.application_id == "APP-001"
        assert callback.status == CallbackStatus.PARTIAL_SUCCESS.value
        assert len(callback.sections) == 2

    def test_partial_success_with_output(self):
        """Partial success with canonical output."""
        sections = [
            SectionStatus(
                section_name="application",
                status="SUCCESS",
            ),
        ]

        callback = PartialSuccessCallback(
            application_id="APP-001",
            sections=sections,
            canonical_output={"applicants": []},
            timestamp="2026-02-11T10:30:00Z",
        )

        callback_dict = callback.to_dict()

        assert callback_dict["canonical_output"] == {"applicants": []}
        assert len(callback_dict["sections"]) == 1


class TestCallbackHTTPAdapter:
    """Test callback HTTP adapter."""

    @pytest.mark.asyncio
    async def test_send_async_returns_response(self):
        """Async send should return response dict."""
        adapter = CallbackHTTPAdapter()

        response = await adapter.send_async(
            callback_url="https://example.com/callback",
            payload={"status": "SUCCESS"},
        )

        assert response["status"] == "sent"
        assert response["url"] == "https://example.com/callback"
        assert "timestamp" in response

    def test_send_sync_returns_response(self):
        """Sync send should return response dict."""
        adapter = CallbackHTTPAdapter()

        response = adapter.send_sync(
            callback_url="https://example.com/callback",
            payload={"status": "SUCCESS"},
        )

        assert response["status"] == "sent"
        assert response["url"] == "https://example.com/callback"
        assert "timestamp" in response

    def test_callback_send_error(self):
        """CallbackSendError should format message properly."""
        error = CallbackSendError(
            message="Connection timeout",
            url="https://example.com/callback",
            status_code=500,
        )

        error_str = str(error)
        assert "https://example.com/callback" in error_str
        assert "Connection timeout" in error_str
        assert "500" in error_str


class TestEvidenceRepository:
    """Test evidence repository."""

    @pytest.mark.asyncio
    async def test_store_evidence_path(self):
        """Store evidence in repository."""
        repo = InMemoryEvidenceRepository()

        record = await repo.store_evidence_path(
            application_id="APP-001",
            evidence_id="EV-001",
            evidence_type="validation",
            path="/validations/email.json",
            source="email_validator",
            entity_type="applicant",
            entity_id="APPL-001",
            rule_id="EMAIL_FORMAT",
        )

        assert record["id"] == "EV-001"
        assert record["application_id"] == "APP-001"
        assert record["type"] == "validation"
        assert record["path"] == "/validations/email.json"

    @pytest.mark.asyncio
    async def test_get_evidence_by_application(self):
        """Retrieve all evidence for application."""
        repo = InMemoryEvidenceRepository()

        await repo.store_evidence_path(
            application_id="APP-001",
            evidence_id="EV-001",
            evidence_type="validation",
            path="/path1.json",
            source="validator1",
        )

        await repo.store_evidence_path(
            application_id="APP-001",
            evidence_id="EV-002",
            evidence_type="enrichment",
            path="/path2.json",
            source="enricher1",
        )

        await repo.store_evidence_path(
            application_id="APP-002",
            evidence_id="EV-003",
            evidence_type="validation",
            path="/path3.json",
            source="validator2",
        )

        app001_evidence = await repo.get_evidence_by_application("APP-001")

        assert len(app001_evidence) == 2
        ids = {e["id"] for e in app001_evidence}
        assert ids == {"EV-001", "EV-002"}

    @pytest.mark.asyncio
    async def test_get_evidence_by_id(self):
        """Retrieve specific evidence by ID."""
        repo = InMemoryEvidenceRepository()

        await repo.store_evidence_path(
            application_id="APP-001",
            evidence_id="EV-001",
            evidence_type="validation",
            path="/path1.json",
            source="validator1",
        )

        evidence = await repo.get_evidence_by_id("EV-001")

        assert evidence is not None
        assert evidence["id"] == "EV-001"
        assert evidence["path"] == "/path1.json"

    @pytest.mark.asyncio
    async def test_get_evidence_not_found(self):
        """Getting non-existent evidence should return None."""
        repo = InMemoryEvidenceRepository()

        evidence = await repo.get_evidence_by_id("EV-NONEXISTENT")

        assert evidence is None

    @pytest.mark.asyncio
    async def test_delete_evidence(self):
        """Delete evidence by ID."""
        repo = InMemoryEvidenceRepository()

        await repo.store_evidence_path(
            application_id="APP-001",
            evidence_id="EV-001",
            evidence_type="validation",
            path="/path1.json",
            source="validator1",
        )

        deleted = await repo.delete_evidence("EV-001")
        assert deleted is True

        evidence = await repo.get_evidence_by_id("EV-001")
        assert evidence is None

    @pytest.mark.asyncio
    async def test_delete_evidence_not_found(self):
        """Deleting non-existent evidence should return False."""
        repo = InMemoryEvidenceRepository()

        deleted = await repo.delete_evidence("EV-NONEXISTENT")
        assert deleted is False


class TestCallbackIntegration:
    """Integration tests for callbacks and evidence."""

    @pytest.mark.asyncio
    async def test_success_flow(self):
        """Test complete success flow."""
        adapter = CallbackHTTPAdapter()
        repo = InMemoryEvidenceRepository()

        # Store evidence
        await repo.store_evidence_path(
            application_id="APP-001",
            evidence_id="EV-001",
            evidence_type="validation",
            path="/validations/email.json",
            source="email_validator",
            entity_type="applicant",
            entity_id="APPL-001",
        )

        # Create success callback
        callback = SuccessCallback(
            application_id="APP-001",
            canonical_output={"applicants": []},
            timestamp="2026-02-11T10:30:00Z",
        )

        # Send callback
        response = await adapter.send_async(
            callback_url="https://example.com/success",
            payload=callback.to_dict(),
        )

        # Verify
        assert response["status"] == "sent"
        evidence = await repo.get_evidence_by_id("EV-001")
        assert evidence is not None

    @pytest.mark.asyncio
    async def test_failure_flow(self):
        """Test complete failure flow."""
        adapter = CallbackHTTPAdapter()

        errors = [
            ErrorDetail(
                field="email",
                code="INVALID_EMAIL",
                message="Email format is invalid",
            )
        ]

        callback = FailureCallback(
            application_id="APP-001",
            error_code="VALIDATION_FAILED",
            error_message="Validation failed for applicant",
            errors=errors,
            timestamp="2026-02-11T10:30:00Z",
        )

        response = await adapter.send_async(
            callback_url="https://example.com/failure",
            payload=callback.to_dict(),
        )

        assert response["status"] == "sent"
        assert callback.to_dict()["error_code"] == "VALIDATION_FAILED"

    @pytest.mark.asyncio
    async def test_partial_success_flow(self):
        """Test complete partial success flow."""
        adapter = CallbackHTTPAdapter()

        sections = [
            SectionStatus(
                section_name="applicants",
                status="SUCCESS",
            ),
            SectionStatus(
                section_name="enrichment",
                status="FAILURE",
                error_message="Credit check failed",
            ),
        ]

        callback = PartialSuccessCallback(
            application_id="APP-001",
            sections=sections,
            canonical_output={"applicants": []},
            timestamp="2026-02-11T10:30:00Z",
        )

        response = await adapter.send_async(
            callback_url="https://example.com/partial",
            payload=callback.to_dict(),
        )

        assert response["status"] == "sent"
        callback_dict = callback.to_dict()
        assert len(callback_dict["sections"]) == 2
        assert callback_dict["sections"][0]["status"] == "SUCCESS"
        assert callback_dict["sections"][1]["status"] == "FAILURE"
