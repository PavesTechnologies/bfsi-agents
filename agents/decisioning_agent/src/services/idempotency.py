from src.core.exceptions import (
    DuplicateRequestInProgressError,
    IdempotencyConflictError,
)


def resolve_idempotent_response(existing_record, application_id: str, request_hash: str):
    if not existing_record:
        return None

    if existing_record.request_hash != request_hash:
        raise IdempotencyConflictError(application_id)

    if existing_record.status == "COMPLETED" and existing_record.response_payload:
        return existing_record.response_payload

    if existing_record.status == "PROCESSING":
        raise DuplicateRequestInProgressError(application_id)

    return None
