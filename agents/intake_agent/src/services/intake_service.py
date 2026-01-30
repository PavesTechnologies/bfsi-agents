import logging
from uuid import UUID, uuid4
from typing import Dict, Any

from src.models.job import Job
from src.core.container import job_executor
from src.repositories.callback_repository import CallbackRepository
from src.services.idempotency_guard import IdempotencyGuard

logger = logging.getLogger(__name__)


class IntakeService:

    def __init__(self, idempotency: IdempotencyGuard , callback_repo: CallbackRepository):
        self.idempotency = idempotency
        self.callback_repo = callback_repo


    async def intake(
        self,
        request_id: UUID,
        app_id: str,
        payload: Dict[str, Any],
        callback_url: str | None,
    ) -> Dict[str, Any]:

        async def first_execution():
            # Register callback FIRST
            if callback_url:
                await self.callback_repo.create_if_not_exists(
                    request_id=request_id,
                    callback_url=str(callback_url),
                )
            job = Job(
                job_id=uuid4(),
                request_id=request_id,
                job_type="intake",
                payload=payload,
            )

            await job_executor.enqueue(job)

            return {
                "request_id": str(request_id),
                "status": "accepted",
            }

        return await self.idempotency.execute(
            request_id=request_id,
            app_id=app_id,
            payload=payload,
            on_first_execution=first_execution,
        )
