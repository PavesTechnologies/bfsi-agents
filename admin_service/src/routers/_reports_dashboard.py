"""GET /reports/dashboard — dashboard KPI aggregation endpoint."""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import cast, func, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_admin_db, get_decisioning_db, get_disbursement_db, get_intake_db
from src.dependencies import require_officer
from src.models.admin_models import LenderUser, HumanReviewQueue
from src.models.external_models import (
    disbursement_records_table,
    loan_application_table,
    underwriting_decisions_table,
)
from src.schemas.reports import DashboardResponse

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    period_days: int = Query(30, ge=1),
    _current_user: LenderUser = Depends(require_officer),
    admin_db: AsyncSession = Depends(get_admin_db),
    intake_db: AsyncSession = Depends(get_intake_db),
    decisioning_db: AsyncSession = Depends(get_decisioning_db),
    disbursement_db: AsyncSession = Depends(get_disbursement_db),
) -> DashboardResponse:
    now_utc = datetime.now(UTC)
    period_cutoff = now_utc - timedelta(days=period_days)
    today_midnight = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)

    # -----------------------------------------------------------------------
    # total_applications — COUNT from loan_application within period
    # -----------------------------------------------------------------------
    stmt_total_apps = select(func.count()).where(
        loan_application_table.c.created_at >= period_cutoff
    )
    result_total_apps = await intake_db.execute(stmt_total_apps)
    total_applications: int = result_total_apps.scalar() or 0

    # -----------------------------------------------------------------------
    # pending_review — COUNT human_review_queue WHERE status = 'PENDING'
    # -----------------------------------------------------------------------
    stmt_pending = select(func.count()).where(HumanReviewQueue.status == "PENDING")
    result_pending = await admin_db.execute(stmt_pending)
    pending_review: int = result_pending.scalar() or 0

    # -----------------------------------------------------------------------
    # in_review — COUNT human_review_queue WHERE status = 'IN_REVIEW'
    # -----------------------------------------------------------------------
    stmt_in_review = select(func.count()).where(HumanReviewQueue.status == "IN_REVIEW")
    result_in_review = await admin_db.execute(stmt_in_review)
    in_review: int = result_in_review.scalar() or 0

    # -----------------------------------------------------------------------
    # approved_today — COUNT WHERE status = 'APPROVED' AND decided_at >= today midnight
    # -----------------------------------------------------------------------
    stmt_approved_today = select(func.count()).where(
        HumanReviewQueue.status == "APPROVED",
        HumanReviewQueue.decided_at >= today_midnight,
    )
    result_approved_today = await admin_db.execute(stmt_approved_today)
    approved_today: int = result_approved_today.scalar() or 0

    # -----------------------------------------------------------------------
    # rejected_today — COUNT WHERE status = 'REJECTED' AND decided_at >= today midnight
    # -----------------------------------------------------------------------
    stmt_rejected_today = select(func.count()).where(
        HumanReviewQueue.status == "REJECTED",
        HumanReviewQueue.decided_at >= today_midnight,
    )
    result_rejected_today = await admin_db.execute(stmt_rejected_today)
    rejected_today: int = result_rejected_today.scalar() or 0

    # -----------------------------------------------------------------------
    # total_disbursed_amount — SUM(disbursement_amount) within period
    # -----------------------------------------------------------------------
    stmt_disbursed = select(
        func.coalesce(func.sum(disbursement_records_table.c.disbursement_amount), 0.0)
    ).where(disbursement_records_table.c.created_at >= period_cutoff)
    result_disbursed = await disbursement_db.execute(stmt_disbursed)
    total_disbursed_amount: float = float(result_disbursed.scalar() or 0.0)

    # -----------------------------------------------------------------------
    # avg_risk_score — AVG(risk_score) from underwriting_decisions within period
    # -----------------------------------------------------------------------
    stmt_avg_risk = select(
        func.coalesce(func.avg(underwriting_decisions_table.c.risk_score), 0.0)
    ).where(underwriting_decisions_table.c.created_at >= period_cutoff)
    result_avg_risk = await decisioning_db.execute(stmt_avg_risk)
    avg_risk_score: float = float(result_avg_risk.scalar() or 0.0)

    # -----------------------------------------------------------------------
    # approval_rate_percent — APPROVED / (APPROVED + REJECTED) * 100
    #                         from human_review_queue within period
    # -----------------------------------------------------------------------
    stmt_approved_period = select(func.count()).where(
        HumanReviewQueue.status == "APPROVED",
        HumanReviewQueue.created_at >= period_cutoff,
    )
    stmt_rejected_period = select(func.count()).where(
        HumanReviewQueue.status == "REJECTED",
        HumanReviewQueue.created_at >= period_cutoff,
    )
    result_approved_period = await admin_db.execute(stmt_approved_period)
    result_rejected_period = await admin_db.execute(stmt_rejected_period)
    approved_count: int = result_approved_period.scalar() or 0
    rejected_count: int = result_rejected_period.scalar() or 0
    denominator = approved_count + rejected_count
    approval_rate_percent: float = (approved_count / denominator * 100.0) if denominator > 0 else 0.0

    # -----------------------------------------------------------------------
    # avg_loan_amount — AVG(requested_amount) from loan_application within period
    # -----------------------------------------------------------------------
    stmt_avg_loan = select(
        func.coalesce(func.avg(loan_application_table.c.requested_amount), 0.0)
    ).where(loan_application_table.c.created_at >= period_cutoff)
    result_avg_loan = await intake_db.execute(stmt_avg_loan)
    avg_loan_amount: float = float(result_avg_loan.scalar() or 0.0)

    # -----------------------------------------------------------------------
    # avg_processing_time_hours — AVG of (uw.created_at - app.created_at) in hours
    #   joined on application_id (cast UUID to String) within period
    # -----------------------------------------------------------------------
    app = loan_application_table.alias("app")
    uw = underwriting_decisions_table.alias("uw")

    processing_time_expr = (
        func.extract(
            "EPOCH",
            uw.c.created_at - app.c.created_at,
        )
        / 3600.0
    )

    stmt_proc_time = (
        select(func.coalesce(func.avg(processing_time_expr), 0.0))
        .select_from(
            app.join(
                uw,
                cast(app.c.application_id, String) == uw.c.application_id,
            )
        )
        .where(app.c.created_at >= period_cutoff)
    )
    # This query spans two separate databases — it cannot be executed as a
    # single SQL join.  We instead compute it in Python: fetch per-application
    # created_at from intake_db, then fetch underwriting created_at from
    # decisioning_db, and compute the average delta in Python.

    stmt_app_times = select(
        cast(loan_application_table.c.application_id, String),
        loan_application_table.c.created_at,
    ).where(loan_application_table.c.created_at >= period_cutoff)
    result_app_times = await intake_db.execute(stmt_app_times)
    app_rows = result_app_times.fetchall()

    avg_processing_time_hours: float = 0.0
    if app_rows:
        app_id_map = {row[0]: row[1] for row in app_rows}
        app_ids = list(app_id_map.keys())

        stmt_uw_times = select(
            underwriting_decisions_table.c.application_id,
            underwriting_decisions_table.c.created_at,
        ).where(underwriting_decisions_table.c.application_id.in_(app_ids))
        result_uw_times = await decisioning_db.execute(stmt_uw_times)
        uw_rows = result_uw_times.fetchall()

        deltas_hours = []
        for uw_app_id, uw_created_at in uw_rows:
            app_created_at = app_id_map.get(uw_app_id)
            if app_created_at is not None and uw_created_at is not None:
                # Ensure both datetimes are timezone-aware for subtraction
                app_dt = app_created_at
                uw_dt = uw_created_at
                if hasattr(app_dt, "tzinfo") and app_dt.tzinfo is None:
                    from datetime import timezone
                    app_dt = app_dt.replace(tzinfo=timezone.utc)
                if hasattr(uw_dt, "tzinfo") and uw_dt.tzinfo is None:
                    from datetime import timezone
                    uw_dt = uw_dt.replace(tzinfo=timezone.utc)
                delta_seconds = (uw_dt - app_dt).total_seconds()
                deltas_hours.append(delta_seconds / 3600.0)

        if deltas_hours:
            avg_processing_time_hours = sum(deltas_hours) / len(deltas_hours)

    return DashboardResponse(
        total_applications=int(total_applications),
        pending_review=int(pending_review),
        in_review=int(in_review),
        approved_today=int(approved_today),
        rejected_today=int(rejected_today),
        total_disbursed_amount=float(total_disbursed_amount),
        avg_risk_score=float(avg_risk_score),
        approval_rate_percent=float(approval_rate_percent),
        avg_loan_amount=float(avg_loan_amount),
        avg_processing_time_hours=float(avg_processing_time_hours),
    )
