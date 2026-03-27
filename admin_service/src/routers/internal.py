"""
Internal webhook endpoints — no auth, service-to-service only.
Called by orchestrator after underwriting to enqueue applications for human review.
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_admin_db
from src.models.admin_models import HumanReviewQueue

router = APIRouter(prefix="/internal", tags=["internal"])


class ReviewQueueWebhookPayload(BaseModel):
    application_id: str
    ai_decision: str
    ai_risk_tier: Optional[str] = None
    ai_risk_score: Optional[float] = None
    ai_suggested_amount: Optional[float] = None
    ai_suggested_rate: Optional[float] = None
    ai_suggested_tenure: Optional[int] = None
    ai_counter_options: Optional[Any] = None
    ai_reasoning: Optional[Any] = None
    ai_decline_reason: Optional[str] = None


@router.post("/review-queue", status_code=201)
async def create_review_queue_entry(
    payload: ReviewQueueWebhookPayload,
    db: AsyncSession = Depends(get_admin_db),
):
    """
    Idempotent: creates a HumanReviewQueue row for the given application.
    Called by the orchestrator immediately after AI underwriting completes.
    """
    existing = await db.execute(
        select(HumanReviewQueue).where(
            HumanReviewQueue.application_id == payload.application_id
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_exists"}

    entry = HumanReviewQueue(
        application_id=payload.application_id,
        status="PENDING",
        ai_decision=payload.ai_decision,
        ai_risk_tier=payload.ai_risk_tier,
        ai_risk_score=payload.ai_risk_score,
        ai_suggested_amount=payload.ai_suggested_amount,
        ai_suggested_rate=payload.ai_suggested_rate,
        ai_suggested_tenure=payload.ai_suggested_tenure,
        ai_counter_options=payload.ai_counter_options,
        ai_reasoning=payload.ai_reasoning,
        ai_decline_reason=payload.ai_decline_reason,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {"status": "created", "queue_id": str(entry.id)}
