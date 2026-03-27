"""
Human review queue management endpoints.
Bank officers assign items to themselves and submit approve/reject decisions.
Decisions are forwarded to the orchestrator to resume or terminate the pipeline.
"""
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.exceptions import ForbiddenException, NotFoundException
from src.db.session import get_admin_db
from src.dependencies import require_officer
from src.models.admin_models import HumanReviewDecision, HumanReviewQueue, LenderUser
from src.schemas.review_queue import (
    DecideRequest,
    DecideResponse,
    PaginatedReviewQueueResponse,
    ReviewQueueItemSchema,
)

router = APIRouter(prefix="/review-queue", tags=["review-queue"])


async def _get_or_404(queue_id: str, db: AsyncSession) -> HumanReviewQueue:
    result = await db.execute(
        select(HumanReviewQueue).where(HumanReviewQueue.id == queue_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise NotFoundException(f"Queue item {queue_id} not found")
    return item


def _to_schema(item: HumanReviewQueue, assignee_name: Optional[str] = None) -> ReviewQueueItemSchema:
    return ReviewQueueItemSchema(
        id=str(item.id),
        application_id=item.application_id,
        status=item.status,
        assigned_to=str(item.assigned_to) if item.assigned_to else None,
        assignee_name=assignee_name,
        ai_decision=item.ai_decision,
        ai_risk_tier=item.ai_risk_tier,
        ai_risk_score=item.ai_risk_score,
        ai_suggested_amount=item.ai_suggested_amount,
        ai_suggested_rate=item.ai_suggested_rate,
        ai_suggested_tenure=item.ai_suggested_tenure,
        ai_counter_options=item.ai_counter_options,
        ai_reasoning=item.ai_reasoning,
        ai_decline_reason=item.ai_decline_reason,
        created_at=item.created_at,
        assigned_at=item.assigned_at,
        decided_at=item.decided_at,
    )


@router.get("", response_model=PaginatedReviewQueueResponse)
async def list_review_queue(
    status: Optional[str] = Query(None, description="PENDING, ASSIGNED, APPROVED, REJECTED, OVERRIDDEN"),
    ai_decision: Optional[str] = Query(None, description="Filter by AI decision (APPROVE, COUNTER_OFFER)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _user: LenderUser = Depends(require_officer),
    db: AsyncSession = Depends(get_admin_db),
):
    q = select(HumanReviewQueue)
    if status:
        q = q.where(HumanReviewQueue.status == status)
    if ai_decision:
        q = q.where(HumanReviewQueue.ai_decision == ai_decision)

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar() or 0

    data_result = await db.execute(
        q.order_by(HumanReviewQueue.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = data_result.scalars().all()

    schemas = []
    for item in items:
        assignee_name = None
        if item.assigned_to:
            u = await db.get(LenderUser, item.assigned_to)
            assignee_name = u.full_name if u else None
        schemas.append(_to_schema(item, assignee_name))

    return PaginatedReviewQueueResponse(total=total, page=page, page_size=page_size, items=schemas)


@router.get("/{queue_id}", response_model=ReviewQueueItemSchema)
async def get_review_queue_item(
    queue_id: str,
    _user: LenderUser = Depends(require_officer),
    db: AsyncSession = Depends(get_admin_db),
):
    item = await _get_or_404(queue_id, db)
    assignee_name = None
    if item.assigned_to:
        u = await db.get(LenderUser, item.assigned_to)
        assignee_name = u.full_name if u else None
    return _to_schema(item, assignee_name)


@router.post("/{queue_id}/assign", response_model=ReviewQueueItemSchema)
async def assign_queue_item(
    queue_id: str,
    current_user: LenderUser = Depends(require_officer),
    db: AsyncSession = Depends(get_admin_db),
):
    """Self-assign a queue item to the current user."""
    item = await _get_or_404(queue_id, db)
    if item.status not in ("PENDING", "ASSIGNED"):
        raise ForbiddenException(f"Cannot assign item with status '{item.status}'")

    item.assigned_to = current_user.id
    item.assigned_at = datetime.now(timezone.utc)
    item.status = "ASSIGNED"
    await db.commit()
    await db.refresh(item)
    return _to_schema(item, current_user.full_name)


@router.post("/{queue_id}/decide", response_model=DecideResponse)
async def decide_queue_item(
    queue_id: str,
    body: DecideRequest,
    current_user: LenderUser = Depends(require_officer),
    db: AsyncSession = Depends(get_admin_db),
):
    """
    Submit a human review decision.
    - APPROVED / OVERRIDDEN → calls orchestrator /human_review/approve → disbursement proceeds
    - REJECTED → calls orchestrator /human_review/reject → pipeline terminates
    """
    if body.decision not in ("APPROVED", "REJECTED", "OVERRIDDEN"):
        raise ForbiddenException("decision must be APPROVED, REJECTED, or OVERRIDDEN")

    item = await _get_or_404(queue_id, db)
    if item.status in ("APPROVED", "REJECTED", "OVERRIDDEN"):
        raise ForbiddenException(f"Queue item already decided (status: {item.status})")

    settings = get_settings()
    orchestrator_notified = False

    async with httpx.AsyncClient(timeout=30) as client:
        if body.decision in ("APPROVED", "OVERRIDDEN"):
            resp = await client.post(
                f"{settings.orchestrator_url}/human_review/approve",
                json={
                    "application_id": item.application_id,
                    "override_amount": body.override_amount,
                    "override_rate": body.override_rate,
                    "override_tenure": body.override_tenure,
                    "selected_offer_id": body.selected_offer_id,
                },
            )
            orchestrator_notified = resp.is_success
        else:
            resp = await client.post(
                f"{settings.orchestrator_url}/human_review/reject",
                json={
                    "application_id": item.application_id,
                    "notes": body.notes,
                },
            )
            orchestrator_notified = resp.is_success

    now = datetime.now(timezone.utc)
    item.status = body.decision
    item.decided_at = now

    db.add(HumanReviewDecision(
        queue_id=item.id,
        application_id=item.application_id,
        reviewed_by=current_user.id,
        decision=body.decision,
        override_amount=body.override_amount,
        override_rate=body.override_rate,
        override_tenure=body.override_tenure,
        selected_offer_id=body.selected_offer_id,
        notes=body.notes,
    ))
    await db.commit()

    return DecideResponse(
        queue_id=str(item.id),
        decision=body.decision,
        status=item.status,
        orchestrator_notified=orchestrator_notified,
    )
