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
