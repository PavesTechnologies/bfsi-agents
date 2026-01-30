import asyncio
import logging
from datetime import datetime

from src.models.job import Job
from src.services.job_executor import JobExecutor
from src.services.job_dispatcher import job_dispatcher
import contextvars

logger = logging.getLogger(__name__)

# down the line we might have other executors (e.g.,KafkaJobExecutor, CeleryJobExecutor)
class InProcessJobExecutor(JobExecutor):

    async def enqueue(self, job: Job) -> None:
        logger.info(
            "job_queued",
            extra={
                "job_id": str(job.job_id),
                "job_type": job.job_type,
                "request_id": str(job.request_id),
            },
        )

        # Fire-and-forget execution -- with context
        ctx = contextvars.copy_context()
        asyncio.create_task(ctx.run(self._run, job))

    async def _run(self, job: Job) -> None:
        start = datetime.utcnow()

        try:
            logger.info(
                "job_started",
                extra={
                    "job_id": str(job.job_id),
                    "job_type": job.job_type,
                    "request_id": str(job.request_id),
                },
            )

            handler = job_dispatcher.get(job.job_type)
            if not handler:
                raise ValueError(f"Unknown job_type: {job.job_type}")

            await handler(job)

            logger.info(
                "job_completed",
                extra={
                    "job_id": str(job.job_id),
                    "job_type": job.job_type,
                    "duration_ms": int(
                        (datetime.utcnow() - start).total_seconds() * 1000
                    ),
                    "request_id": str(job.request_id),
                },
            )

        except Exception:
            logger.exception(
                "job_failed",
                extra={
                    "job_id": str(job.job_id),
                    "job_type": job.job_type,
                    "request_id": str(job.request_id),
                },
            )
