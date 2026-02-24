import logging
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from src.core.exceptions import PayloadMismatchError
from src.repositories.idempotency_repository import IdempotencyRepository
from src.utils.hash import stable_payload_hash

logger = logging.getLogger(__name__)


class IdempotencyGuard:
    def __init__(self, repo: IdempotencyRepository):
        self.repo = repo

    async def execute(
        self,
        *,
        request_id: UUID,
        app_id: str,
        payload: dict[str, Any],
        on_first_execution: Callable[[], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        payload_hash = stable_payload_hash(payload)

        existing = await self.repo.get(request_id)

        if existing:
            if existing.request_hash != payload_hash:
                raise PayloadMismatchError(request_id)

            if existing.status == "COMPLETED":
                return existing.response_payload

            # If request is already in progress
            raise RuntimeError("Duplicate request is currently processing")

        await self.repo.create(
            request_id=request_id,
            app_id=app_id,
            request_hash=payload_hash,
        )

        return await on_first_execution()
