from fastapi import Request


def resolve_correlation_id(
    request: Request,
    payload_correlation_id: str | None,
    application_id: str,
) -> str:
    return (
        payload_correlation_id
        or request.headers.get("x-correlation-id")
        or request.headers.get("x-request-id")
        or application_id
    )
