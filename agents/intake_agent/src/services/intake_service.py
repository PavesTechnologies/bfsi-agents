import logging
from typing import Any
from uuid import UUID, uuid4

from src.core.container import job_executor
from src.models.job import Job
from src.models.metadata import RequestMetadata
from src.repositories.callback_repository import CallbackRepository
from src.repositories.metadata_repository import MetadataRepository
from src.services.idempotency_guard import IdempotencyGuard

logger = logging.getLogger(__name__)


class IntakeService:
    def __init__(
        self,
        idempotency: IdempotencyGuard,
        callback_repo: CallbackRepository,
        metadata_repo: MetadataRepository,
    ):
        """Initialize IntakeService with required dependencies.

        Args:
            idempotency: Idempotency guard for deduplication
            callback_repo: Repository for callback tracking
            metadata_repo: Repository for metadata persistence (REQUIRED)
        """
        self.idempotency = idempotency
        self.callback_repo = callback_repo
        self.metadata_repo = metadata_repo

    async def intake(
        self,
        request_id: UUID,
        app_id: str,
        payload: dict[str, Any],
        callback_url: str | None,
        metadata: RequestMetadata,
    ) -> dict[str, Any]:
        """
        Process intake request with mandatory metadata capture.

        Args:
            request_id: Unique request identifier
            app_id: Application identifier
            payload: Request payload
            callback_url: Optional callback URL for async processing
            metadata: Request metadata (REQUIRED) - IP, device info, headers, etc.

        Returns:
            Response with request status

        Raises:
            Exception: On metadata persistence failure (intentional - fails intake)
        """

        async def first_execution():
            # Store metadata - MANDATORY. Failure raises exception.
            await self.metadata_repo.create(
                request_id=request_id,
                app_id=UUID(app_id) if isinstance(app_id, str) else app_id,
                metadata=metadata,
            )

            logger.info(
                "Metadata and intake request stored",
                extra={
                    "request_id": str(request_id),
                    "ip_address": metadata.ip_address,
                    "device_type": metadata.device_type,
                },
            )

            # Register callback AFTER metadata is safely persisted
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
