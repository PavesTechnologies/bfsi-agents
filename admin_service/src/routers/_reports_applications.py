"""GET /reports/applications — Applications report with chart data and summary."""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import cast, func, select, String, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_admin_db, get_decisioning_db, get_intake_db
from src.dependencies import require_officer
from src.models.admin_models import HumanReviewQueue, LenderUser
from src.models.external_models import loan_application_table, underwriting_decisions_table
from src.schemas.reports import (
    ApplicationChartPoint,
    ApplicationsReportResponse,
    ApplicationsSummary,
)

router = APIRouter()


@router.get("/applications", response_model=ApplicationsReportResponse)
async def get_applications_report(
    period_days: int = Query(30, ge=1),
    group_by: str = Query("day", pattern="^(day|week|month)$"),
    _current_user: LenderUser = Depends(require_officer),
    admin_db: AsyncSession = Depends(get_admin_db),
    intake_db: AsyncSession = Depends(get_intake_db),
    decisioning_db: AsyncSession = Depends(get_decisioning_db),
) -> ApplicationsReportResponse:
    cutoff = datetime.now(UTC) - timedelta(days=period_days)

    # ------------------------------------------------------------------
    # chart_data: loan_application and underwriting_decisions live in
    # separate databases (defaultdb / decisioning_agent) — they cannot be
    # joined in a single SQL query.  Fetch each side independently, then
    # merge in Python by application_id.
    # ------------------------------------------------------------------
    la = loan_application_table
    ud = underwriting_decisions_table

    # 1. Fetch (application_id, created_at) from intake_db
    app_stmt = select(
        cast(la.c.application_id, String).label("app_id"),
        la.c.created_at,
    ).where(la.c.created_at >= cutoff)
    app_rows = (await intake_db.execute(app_stmt)).fetchall()

    # 2. Fetch (application_id, decision) from decisioning_db
    dec_stmt = select(
        ud.c.application_id,
        ud.c.decision,
    ).where(ud.c.created_at >= cutoff)
    dec_rows = (await decisioning_db.execute(dec_stmt)).fetchall()
    decision_map: dict[str, str] = {row.application_id: row.decision for row in dec_rows}

    # 3. Bucket each application in Python
    def _trunc(dt: datetime, bucket: str) -> datetime:
        if bucket == "day":
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
        if bucket == "week":
            return (dt - timedelta(days=dt.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        # month
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    from collections import defaultdict
    bucket_data: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "approved": 0, "declined": 0, "counter_offer": 0}
    )
    for row in app_rows:
        app_id = row.app_id
        created = row.created_at
        if created.tzinfo is None:
            from datetime import timezone
            created = created.replace(tzinfo=timezone.utc)
        key = _trunc(created, group_by).strftime("%Y-%m-%d")
        b = bucket_data[key]
        b["total"] += 1
        dec = decision_map.get(app_id)
        if dec == "APPROVE":
            b["approved"] += 1
        elif dec == "DECLINE":
            b["declined"] += 1
        elif dec == "COUNTER_OFFER":
            b["counter_offer"] += 1

    chart_data: list[ApplicationChartPoint] = [
        ApplicationChartPoint(
            date=date_str,
            total=b["total"],
            approved=b["approved"],
            declined=b["declined"],
            counter_offer=b["counter_offer"],
            pending=b["total"] - b["approved"] - b["declined"] - b["counter_offer"],
        )
        for date_str, b in sorted(bucket_data.items())
    ]

    # ------------------------------------------------------------------
    # summary counts
    # ------------------------------------------------------------------

    # Total loan applications in period (from intake_db)
    total_stmt = (
        select(func.count())
        .select_from(la)
        .where(la.c.created_at >= cutoff)
    )
    total_result = await intake_db.execute(total_stmt)
    summary_total = int(total_result.scalar() or 0)

    # Approved / declined / counter_offer from underwriting_decisions in period
    decision_stmt = (
        select(
            func.sum(case((ud.c.decision == "APPROVE", 1), else_=0)).label("approved"),
            func.sum(case((ud.c.decision == "DECLINE", 1), else_=0)).label("declined"),
            func.sum(case((ud.c.decision == "COUNTER_OFFER", 1), else_=0)).label("counter_offer"),
        )
        .select_from(ud)
        .where(ud.c.created_at >= cutoff)
    )
    decision_result = await decisioning_db.execute(decision_stmt)
    decision_row = decision_result.fetchone()
    summary_approved = int(decision_row.approved or 0) if decision_row else 0
    summary_declined = int(decision_row.declined or 0) if decision_row else 0
    summary_counter_offer = int(decision_row.counter_offer or 0) if decision_row else 0

    # pending_human_review: human_review_queue WHERE status IN ('PENDING', 'IN_REVIEW')
    pending_hr_stmt = (
        select(func.count())
        .select_from(HumanReviewQueue)
        .where(HumanReviewQueue.status.in_(["PENDING", "IN_REVIEW"]))
    )
    pending_hr_result = await admin_db.execute(pending_hr_stmt)
    pending_human_review = int(pending_hr_result.scalar() or 0)

    # human_rejected: human_review_queue WHERE status = 'REJECTED'
    rejected_hr_stmt = (
        select(func.count())
        .select_from(HumanReviewQueue)
        .where(HumanReviewQueue.status == "REJECTED")
    )
    rejected_hr_result = await admin_db.execute(rejected_hr_stmt)
    human_rejected = int(rejected_hr_result.scalar() or 0)

    summary = ApplicationsSummary(
        total=summary_total,
        approved=summary_approved,
        declined=summary_declined,
        counter_offer=summary_counter_offer,
        pending_human_review=pending_human_review,
        human_rejected=human_rejected,
    )

    return ApplicationsReportResponse(chart_data=chart_data, summary=summary)
