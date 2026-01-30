import logging
from typing import Callable, Awaitable, Dict, Any
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
        payload: Dict[str, Any],
        on_first_execution: Callable[[], Awaitable[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        Enforces idempotency around a unit of work.
        """

        payload_hash = stable_payload_hash(payload)

        existing = await self.repo.get(request_id)

        if existing:
            if existing.request_hash != payload_hash:
                raise PayloadMismatchError(request_id)

            if existing.status == "COMPLETED":
                return existing.response_payload

            return {
                "request_id": str(request_id),
                "status": "accepted",
            }

        await self.repo.create(
            request_id=request_id,
            app_id=app_id,
            request_hash=payload_hash,
        )

        return await on_first_execution()
