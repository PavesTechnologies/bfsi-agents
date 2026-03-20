class IdempotencyConflictError(Exception):
    def __init__(self, application_id: str):
        super().__init__(
            f"application_id '{application_id}' was reused with a different disbursement payload"
        )


class DuplicateRequestInProgressError(Exception):
    def __init__(self, application_id: str):
        super().__init__(
            f"disbursement request for application_id '{application_id}' is already in progress"
        )
