"""GET /reports/review-performance — Officer review performance metrics."""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_admin_db
from src.dependencies import require_manager
from src.models.admin_models import HumanReviewDecision, HumanReviewQueue, LenderUser
from src.schemas.reports import OfficerPerformance, ReviewPerformanceResponse

router = APIRouter()


@router.get("/review-performance", response_model=ReviewPerformanceResponse)
async def get_review_performance(
    period_days: int = Query(30, ge=1),
    _current_user: LenderUser = Depends(require_manager),
    admin_db: AsyncSession = Depends(get_admin_db),
) -> ReviewPerformanceResponse:
    cutoff = datetime.now(UTC) - timedelta(days=period_days)

    # ------------------------------------------------------------------
    # Per-officer aggregates
    # ------------------------------------------------------------------
    avg_time_expr = func.coalesce(
        func.avg(
            func.extract(
                "epoch",
                HumanReviewQueue.decided_at - HumanReviewQueue.assigned_at,
            )
            / 3600
        ),
        0.0,
    )

    officer_stmt = (
        select(
            LenderUser.id.label("officer_id"),
            LenderUser.full_name.label("officer_name"),
            func.count(HumanReviewDecision.id).label("reviewed_count"),
            avg_time_expr.label("avg_review_time_hours"),
            func.sum(
                case((HumanReviewDecision.decision == "APPROVED", 1), else_=0)
            ).label("approved"),
            func.sum(
                case((HumanReviewDecision.decision == "REJECTED", 1), else_=0)
            ).label("rejected"),
            func.sum(
                case((HumanReviewDecision.decision == "APPROVED_WITH_OVERRIDE", 1), else_=0)
            ).label("overridden"),
        )
        .select_from(HumanReviewDecision)
        .join(LenderUser, HumanReviewDecision.reviewed_by == LenderUser.id)
        .join(HumanReviewQueue, HumanReviewDecision.queue_id == HumanReviewQueue.id)
        .where(HumanReviewDecision.created_at >= cutoff)
        .group_by(LenderUser.id, LenderUser.full_name)
        .order_by(LenderUser.full_name)
    )

    officer_result = await admin_db.execute(officer_stmt)
    officer_rows = officer_result.fetchall()

    by_officer: list[OfficerPerformance] = []
    total_reviewed = 0
    total_overridden = 0

    for row in officer_rows:
        reviewed_count = int(row.reviewed_count or 0)
        approved = int(row.approved or 0)
        rejected = int(row.rejected or 0)
        overridden = int(row.overridden or 0)
        total_reviewed += reviewed_count
        total_overridden += overridden

        by_officer.append(
            OfficerPerformance(
                officer_id=str(row.officer_id),
                officer_name=row.officer_name or "",
                reviewed_count=reviewed_count,
                avg_review_time_hours=float(row.avg_review_time_hours or 0.0),
                approved=approved,
                rejected=rejected,
                overridden=overridden,
            )
        )

    # ------------------------------------------------------------------
    # override_rate_percent
    # ------------------------------------------------------------------
    override_rate_percent = (
        (total_overridden / total_reviewed * 100.0) if total_reviewed > 0 else 0.0
    )

    # ------------------------------------------------------------------
    # ai_agreement_rate — fetch all decisions with queue ai_decision in period
    # and compute agreement in Python
    # ------------------------------------------------------------------
    ai_stmt = (
        select(
            HumanReviewDecision.decision.label("officer_decision"),
            HumanReviewQueue.ai_decision.label("ai_decision"),
        )
        .select_from(HumanReviewDecision)
        .join(HumanReviewQueue, HumanReviewDecision.queue_id == HumanReviewQueue.id)
        .where(HumanReviewDecision.created_at >= cutoff)
    )

    ai_result = await admin_db.execute(ai_stmt)
    ai_rows = ai_result.fetchall()

    agreement_count = 0
    total_count = len(ai_rows)

    for row in ai_rows:
        officer_decision = row.officer_decision
        ai_decision = row.ai_decision

        if ai_decision == "APPROVE":
            if officer_decision in ("APPROVED", "APPROVED_WITH_OVERRIDE"):
                agreement_count += 1
        elif ai_decision == "DECLINE":
            if officer_decision == "REJECTED":
                agreement_count += 1
        elif ai_decision == "COUNTER_OFFER":
            if officer_decision in ("APPROVED_WITH_OVERRIDE", "APPROVED"):
                agreement_count += 1

    ai_agreement_rate = (
        (agreement_count / total_count * 100.0) if total_count > 0 else 0.0
    )

    return ReviewPerformanceResponse(
        by_officer=by_officer,
        override_rate_percent=override_rate_percent,
        ai_agreement_rate=ai_agreement_rate,
    )
