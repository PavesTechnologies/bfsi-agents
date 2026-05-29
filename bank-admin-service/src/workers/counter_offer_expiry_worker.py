"""
Counter Offer Expiry Worker

Scans counter_offer_sessions for DRAFT sessions whose expires_at has passed
and marks them EXPIRED. Also transitions the associated application from
COUNTER_OFFER_REVIEW to CANCELLED so the pipeline doesn't stall.

Runs as an asyncio task started in the FastAPI lifespan — no broker or
external scheduler required.
"""
import asyncio
import datetime
import logging

from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.models.counter_offer import CounterOfferSession, CounterOfferStatus
from src.models.loan_application import LoanApplication, PipelineStatus

logger = logging.getLogger(__name__)

_INTERVAL_SECONDS = 3600  # sweep once per hour


async def _expire_stale_sessions() -> int:
    """
    Find all DRAFT sessions past their expires_at, mark them EXPIRED, and
    cancel the corresponding application if it is still in COUNTER_OFFER_REVIEW.

    Returns the number of sessions expired in this run.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    expired_count = 0

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(CounterOfferSession).where(
                    CounterOfferSession.status == CounterOfferStatus.DRAFT,
                    CounterOfferSession.expires_at <= now,
                )
            )
            sessions = result.scalars().all()

            for session in sessions:
                session.status = CounterOfferStatus.EXPIRED
                session.updated_at = now

                # Pull the application and advance it out of review so it
                # doesn't sit stuck in the bank queue indefinitely.
                app_result = await db.execute(
                    select(LoanApplication).where(
                        LoanApplication.id == session.application_id
                    )
                )
                app = app_result.scalar_one_or_none()
                if app and app.pipeline_status == PipelineStatus.COUNTER_OFFER_REVIEW:
                    app.pipeline_status = PipelineStatus.CANCELLED
                    app.updated_at = now

                expired_count += 1

            if expired_count:
                await db.commit()
                logger.info(
                    "counter_offer_expiry: expired %d session(s)", expired_count
                )

        except Exception:
            logger.exception("counter_offer_expiry: error during sweep")
            await db.rollback()

    return expired_count


async def run_expiry_loop(interval_seconds: int = _INTERVAL_SECONDS) -> None:
    """
    Long-running coroutine: run a sweep immediately on startup, then once
    every `interval_seconds`. Designed to be launched via asyncio.create_task
    inside the FastAPI lifespan and cancelled gracefully on shutdown.
    """
    logger.info("counter_offer_expiry: starting (interval=%ds)", interval_seconds)
    while True:
        await _expire_stale_sessions()
        await asyncio.sleep(interval_seconds)
