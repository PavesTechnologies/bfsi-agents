from types import SimpleNamespace

import pytest

from src.core.exceptions import (
    DuplicateRequestInProgressError,
    IdempotencyConflictError,
)
from src.services.idempotency import resolve_idempotent_response


def test_resolve_idempotent_response_returns_cached_payload():
    record = SimpleNamespace(
        request_hash="abc",
        status="COMPLETED",
        response_payload={"application_id": "APP-123"},
    )

    result = resolve_idempotent_response(record, "APP-123", "abc")

    assert result == {"application_id": "APP-123"}


def test_resolve_idempotent_response_raises_on_hash_mismatch():
    record = SimpleNamespace(request_hash="abc", status="COMPLETED", response_payload={})

    with pytest.raises(IdempotencyConflictError):
        resolve_idempotent_response(record, "APP-123", "xyz")


def test_resolve_idempotent_response_raises_when_processing():
    record = SimpleNamespace(request_hash="abc", status="PROCESSING", response_payload=None)

    with pytest.raises(DuplicateRequestInProgressError):
        resolve_idempotent_response(record, "APP-123", "abc")
