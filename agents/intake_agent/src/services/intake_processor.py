import asyncio
import logging

from src.core.database import AsyncSessionLocal
from src.models.job import Job
from src.services.callback_service import CallbackService

logger = logging.getLogger(__name__)


async def process_intake(job: Job) -> None:
    """
    This is where the intake pipeline will live.
    OCR, validation, enrichment, scoring, etc.
    """

    logger.info(
        "intake_processing_started",
        extra={
            "job_id": str(job.job_id),
            "request_id": str(job.request_id),
        },
    )
    # sleep to simulate processing
    await asyncio.sleep(10)

    async with AsyncSessionLocal() as session:
        callback_service = CallbackService(session)

    await callback_service.send_success(
        request_id=str(job.request_id),
        data={"message": "Intake processing completed successfully"},
    )

    # Placeholder for real pipeline
    # Example:
    # from src.workflows.intake_pipeline import run_intake_pipeline
    # result = await run_intake_pipeline(job.payload)

    logger.info("intake_processing_completed", extra={"job_id": str(job.job_id)})
