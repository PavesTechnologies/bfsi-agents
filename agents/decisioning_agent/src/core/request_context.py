import uuid
from typing import Optional
from fastapi import Request

def resolve_correlation_id(
    request: Optional[Request] = None,
    payload_correlation_id: Optional[str] = None,
    application_id: Optional[str] = None,
) -> str:
    """Resolve a correlation ID for tracing the request."""
    if payload_correlation_id:
        return payload_correlation_id
    if request and request.headers.get("x-correlation-id"):
        return request.headers.get("x-correlation-id")
    if application_id:
        return f"app-{application_id}-{uuid.uuid4().hex[:8]}"
    return uuid.uuid4().hex
