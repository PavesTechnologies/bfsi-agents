"""GET /reports/disbursements — disbursement analytics endpoint."""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_disbursement_db
from src.dependencies import require_officer
from src.models.admin_models import LenderUser
from src.models.external_models import disbursement_records_table
from src.schemas.reports import (
    DisbursementChartPoint,
    DisbursementsReportResponse,
    DisbursementsSummary,
)

router = APIRouter()


@router.get("/disbursements", response_model=DisbursementsReportResponse)
async def get_disbursements_report(
    period_days: int = Query(30, ge=1),
    group_by: str = Query("day", pattern="^(day|week|month)$"),
    _current_user: LenderUser = Depends(require_officer),
    disbursement_db: AsyncSession = Depends(get_disbursement_db),
) -> DisbursementsReportResponse:
    cutoff = datetime.now(UTC) - timedelta(days=period_days)

    # -----------------------------------------------------------------------
    # chart_data — GROUP BY DATE_TRUNC(group_by, created_at)
    # -----------------------------------------------------------------------
    date_bucket = func.date_trunc(group_by, disbursement_records_table.c.created_at)

    stmt_chart = (
        select(
            date_bucket.label("bucket"),
            func.count().label("count"),
            func.coalesce(func.sum(disbursement_records_table.c.disbursement_amount), 0).label("total_amount"),
            func.coalesce(func.avg(disbursement_records_table.c.disbursement_amount), 0).label("avg_amount"),
        )
        .where(disbursement_records_table.c.created_at >= cutoff)
        .group_by(date_bucket)
        .order_by(date_bucket.asc())
    )

    result_chart = await disbursement_db.execute(stmt_chart)
    chart_rows = result_chart.fetchall()

    chart_data = [
        DisbursementChartPoint(
            date=row.bucket.strftime("%Y-%m-%d") if row.bucket is not None else "",
            count=int(row.count),
            total_amount=float(row.total_amount),
            avg_amount=float(row.avg_amount),
        )
        for row in chart_rows
    ]

    # -----------------------------------------------------------------------
    # summary — aggregate over the same period
    # -----------------------------------------------------------------------
    stmt_summary = select(
        func.count().label("total_count"),
        func.coalesce(func.sum(disbursement_records_table.c.disbursement_amount), 0).label("total_amount"),
        func.coalesce(func.avg(disbursement_records_table.c.disbursement_amount), 0).label("avg_loan_amount"),
        func.coalesce(func.sum(disbursement_records_table.c.total_interest), 0).label("total_interest_income"),
    ).where(disbursement_records_table.c.created_at >= cutoff)

    result_summary = await disbursement_db.execute(stmt_summary)
    summary_row = result_summary.fetchone()

    summary = DisbursementsSummary(
        total_count=int(summary_row.total_count) if summary_row else 0,
        total_amount=float(summary_row.total_amount) if summary_row else 0.0,
        avg_loan_amount=float(summary_row.avg_loan_amount) if summary_row else 0.0,
        avg_interest_rate=0.0,   # disbursement_records has no interest_rate column
        avg_tenure_months=0.0,   # disbursement_records has no tenure_months column
        total_interest_income=float(summary_row.total_interest_income) if summary_row else 0.0,
    )

    return DisbursementsReportResponse(chart_data=chart_data, summary=summary)
