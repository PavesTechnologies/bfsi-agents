"""
Tests for Callback Service.

Test cases:
- Success callback async sending
- Failure callback async sending
- Partial success callback async sending
- Success callback sync sending
- Failure callback sync sending
- Mock adapter injection for testing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.services.callback_service import CallbackService
from src.domain.callbacks.callback_models import (
    SuccessCallback,
    FailureCallback,
    PartialSuccessCallback,
    ErrorDetail,
    SectionStatus,
)
from src.adapters.callbacks.callback_adapter import CallbackHTTPAdapter


class TestCallbackServiceAsync:
    """Test async callback service methods."""

    @pytest.mark.asyncio
    async def test_send_success_callback_async(self):
        """Send success callback asynchronously."""
        # Create mock adapter
        mock_adapter = AsyncMock(spec=CallbackHTTPAdapter)
        mock_adapter.send_async.return_value = {"status": "sent", "timestamp": "2026-02-11T10:30:00Z"}

        # Create service with mock
        service = CallbackService(adapter=mock_adapter)

        # Create callback
        callback = SuccessCallback(
            application_id="APP-001",
            canonical_output={"applicants": []},
            timestamp="2026-02-11T10:30:00Z",
        )

        # Send
        response = await service.send_success_callback(
            callback_url="https://example.com/success",
            success_callback=callback,
        )

        # Verify
        assert response["status"] == "sent"
        mock_adapter.send_async.assert_called_once()
        call_args = mock_adapter.send_async.call_args
        assert call_args.kwargs["callback_url"] == "https://example.com/success"
        assert call_args.kwargs["payload"]["application_id"] == "APP-001"

    @pytest.mark.asyncio
    async def test_send_failure_callback_async(self):
        """Send failure callback asynchronously."""
        mock_adapter = AsyncMock(spec=CallbackHTTPAdapter)
        mock_adapter.send_async.return_value = {"status": "sent"}

        service = CallbackService(adapter=mock_adapter)

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

        response = await service.send_failure_callback(
            callback_url="https://example.com/failure",
            failure_callback=callback,
        )

        assert response["status"] == "sent"
        mock_adapter.send_async.assert_called_once()
        call_args = mock_adapter.send_async.call_args
        assert call_args.kwargs["payload"]["error_code"] == "VALIDATION_FAILED"

    @pytest.mark.asyncio
    async def test_send_partial_success_callback_async(self):
        """Send partial success callback asynchronously."""
        mock_adapter = AsyncMock(spec=CallbackHTTPAdapter)
        mock_adapter.send_async.return_value = {"status": "sent"}

        service = CallbackService(adapter=mock_adapter)

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

        response = await service.send_partial_success_callback(
            callback_url="https://example.com/partial",
            partial_callback=callback,
        )

        assert response["status"] == "sent"
        mock_adapter.send_async.assert_called_once()
        call_args = mock_adapter.send_async.call_args
        assert len(call_args.kwargs["payload"]["sections"]) == 2


class TestCallbackServiceSync:
    """Test sync callback service methods."""

    def test_send_success_callback_sync(self):
        """Send success callback synchronously."""
        mock_adapter = MagicMock(spec=CallbackHTTPAdapter)
        mock_adapter.send_sync.return_value = {"status": "sent"}

        service = CallbackService(adapter=mock_adapter)

        callback = SuccessCallback(
            application_id="APP-001",
            canonical_output={"applicants": []},
            timestamp="2026-02-11T10:30:00Z",
        )

        response = service.send_success_callback_sync(
            callback_url="https://example.com/success",
            success_callback=callback,
        )

        assert response["status"] == "sent"
        mock_adapter.send_sync.assert_called_once()

    def test_send_failure_callback_sync(self):
        """Send failure callback synchronously."""
        mock_adapter = MagicMock(spec=CallbackHTTPAdapter)
        mock_adapter.send_sync.return_value = {"status": "sent"}

        service = CallbackService(adapter=mock_adapter)

        callback = FailureCallback(
            application_id="APP-001",
            error_code="VALIDATION_FAILED",
            error_message="Validation failed",
            timestamp="2026-02-11T10:30:00Z",
        )

        response = service.send_failure_callback_sync(
            callback_url="https://example.com/failure",
            failure_callback=callback,
        )

        assert response["status"] == "sent"

    def test_send_partial_success_callback_sync(self):
        """Send partial success callback synchronously."""
        mock_adapter = MagicMock(spec=CallbackHTTPAdapter)
        mock_adapter.send_sync.return_value = {"status": "sent"}

        service = CallbackService(adapter=mock_adapter)

        sections = [
            SectionStatus(
                section_name="applicants",
                status="SUCCESS",
            ),
        ]

        callback = PartialSuccessCallback(
            application_id="APP-001",
            sections=sections,
            timestamp="2026-02-11T10:30:00Z",
        )

        response = service.send_partial_success_callback_sync(
            callback_url="https://example.com/partial",
            partial_callback=callback,
        )

        assert response["status"] == "sent"


class TestCallbackServiceDependencyInjection:
    """Test dependency injection of callback service."""

    def test_default_adapter_creation(self):
        """Service should create default adapter if not provided."""
        service = CallbackService()

        assert service.adapter is not None
        assert isinstance(service.adapter, CallbackHTTPAdapter)

    def test_custom_adapter_injection(self):
        """Service should use custom adapter if provided."""
        custom_adapter = MagicMock(spec=CallbackHTTPAdapter)
        service = CallbackService(adapter=custom_adapter)

        assert service.adapter is custom_adapter

    @pytest.mark.asyncio
    async def test_adapter_isolation_async(self):
        """Multiple service instances should not share adapters."""
        adapter1 = AsyncMock(spec=CallbackHTTPAdapter)
        adapter1.send_async.return_value = {"status": "sent1"}

        adapter2 = AsyncMock(spec=CallbackHTTPAdapter)
        adapter2.send_async.return_value = {"status": "sent2"}

        service1 = CallbackService(adapter=adapter1)
        service2 = CallbackService(adapter=adapter2)

        callback = SuccessCallback(
            application_id="APP-001",
            canonical_output={},
            timestamp="2026-02-11T10:30:00Z",
        )

        result1 = await service1.send_success_callback(
            callback_url="https://example1.com",
            success_callback=callback,
        )
        result2 = await service2.send_success_callback(
            callback_url="https://example2.com",
            success_callback=callback,
        )

        assert result1["status"] == "sent1"
        assert result2["status"] == "sent2"
        adapter1.send_async.assert_called_once()
        adapter2.send_async.assert_called_once()


class TestCallbackServicePayloadFormatting:
    """Test that service correctly formats payloads."""

    @pytest.mark.asyncio
    async def test_success_payload_structure(self):
        """Verify success callback payload structure."""
        mock_adapter = AsyncMock(spec=CallbackHTTPAdapter)
        captured_payload = None

        async def capture_payload(callback_url, payload):
            nonlocal captured_payload
            captured_payload = payload
            return {"status": "sent"}

        mock_adapter.send_async.side_effect = capture_payload

        service = CallbackService(adapter=mock_adapter)

        callback = SuccessCallback(
            application_id="APP-123",
            canonical_output={"applicants": [{"id": "APPL-001"}]},
            timestamp="2026-02-11T10:30:00Z",
        )

        await service.send_success_callback(
            callback_url="https://example.com",
            success_callback=callback,
        )

        assert captured_payload["application_id"] == "APP-123"
        assert captured_payload["status"] == "SUCCESS"
        assert "timestamp" in captured_payload
        assert "canonical_output" in captured_payload

    @pytest.mark.asyncio
    async def test_failure_payload_structure(self):
        """Verify failure callback payload structure."""
        mock_adapter = AsyncMock(spec=CallbackHTTPAdapter)
        captured_payload = None

        async def capture_payload(callback_url, payload):
            nonlocal captured_payload
            captured_payload = payload
            return {"status": "sent"}

        mock_adapter.send_async.side_effect = capture_payload

        service = CallbackService(adapter=mock_adapter)

        errors = [
            ErrorDetail(
                field="email",
                code="INVALID",
                message="Invalid email",
            )
        ]

        callback = FailureCallback(
            application_id="APP-001",
            error_code="VALIDATION_ERROR",
            error_message="Validation failed",
            errors=errors,
            timestamp="2026-02-11T10:30:00Z",
        )

        await service.send_failure_callback(
            callback_url="https://example.com",
            failure_callback=callback,
        )

        assert captured_payload["error_code"] == "VALIDATION_ERROR"
        assert captured_payload["status"] == "FAILURE"
        assert len(captured_payload["errors"]) == 1
        assert captured_payload["errors"][0]["field"] == "email"

    @pytest.mark.asyncio
    async def test_partial_success_payload_structure(self):
        """Verify partial success callback payload structure."""
        mock_adapter = AsyncMock(spec=CallbackHTTPAdapter)
        captured_payload = None

        async def capture_payload(callback_url, payload):
            nonlocal captured_payload
            captured_payload = payload
            return {"status": "sent"}

        mock_adapter.send_async.side_effect = capture_payload

        service = CallbackService(adapter=mock_adapter)

        sections = [
            SectionStatus(section_name="applicants", status="SUCCESS"),
            SectionStatus(
                section_name="enrichment",
                status="FAILURE",
                error_message="Service down",
            ),
        ]

        callback = PartialSuccessCallback(
            application_id="APP-001",
            sections=sections,
            canonical_output={"applicants": []},
            timestamp="2026-02-11T10:30:00Z",
        )

        await service.send_partial_success_callback(
            callback_url="https://example.com",
            partial_callback=callback,
        )

        assert captured_payload["status"] == "PARTIAL_SUCCESS"
        assert len(captured_payload["sections"]) == 2
        assert captured_payload["sections"][0]["section_name"] == "applicants"
        assert captured_payload["sections"][1]["error_message"] == "Service down"
