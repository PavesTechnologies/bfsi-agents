from uuid import uuid4

from fastapi import Header
from src.core.logging import request_id_ctx


class DatabaseClient:
    def ping(self) -> bool:
        """
        Lightweight connectivity check.
        Should NOT run queries.
        """
        return True  # Stub implementation


db_client = DatabaseClient()


async def get_request_id(
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    request_id = x_request_id or str(uuid4())

    request_id_ctx.set(request_id)

    return request_id
