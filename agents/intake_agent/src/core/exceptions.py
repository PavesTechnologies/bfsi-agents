from fastapi import status


class BaseAgentException(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "internal_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ConfigError(BaseAgentException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "config_error"


class AsyncExecutionError(BaseAgentException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "async_execution_error"

class PayloadMismatchError(BaseAgentException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "payload_mismatch"

    def __init__(self, request_id):
        message = f"Payload mismatch for request_id: {request_id}"
        super().__init__(message)
