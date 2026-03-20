from starlette.requests import Request

from src.core.request_context import resolve_correlation_id


def test_resolve_correlation_id_prefers_explicit_payload_value():
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/underwrite",
        "headers": [(b"x-correlation-id", b"REQ-789")],
    }

    assert (
        resolve_correlation_id(Request(scope), "PAYLOAD-123", "APP-123")
        == "PAYLOAD-123"
    )


def test_resolve_correlation_id_falls_back_to_headers_then_application_id():
    header_scope = {
        "type": "http",
        "method": "POST",
        "path": "/underwrite",
        "headers": [(b"x-request-id", b"REQ-456")],
    }
    empty_scope = {
        "type": "http",
        "method": "POST",
        "path": "/underwrite",
        "headers": [],
    }

    assert (
        resolve_correlation_id(Request(header_scope), None, "APP-123")
        == "REQ-456"
    )
    assert (
        resolve_correlation_id(Request(empty_scope), None, "APP-123")
        == "APP-123"
    )
