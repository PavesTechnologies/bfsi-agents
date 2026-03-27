"""GET /reports/risk-distribution — risk tier breakdown and score histogram."""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_decisioning_db
from src.dependencies import require_officer
from src.models.admin_models import LenderUser
from src.models.external_models import underwriting_decisions_table
from src.schemas.reports import RiskByTier, RiskDistributionResponse, ScoreHistogramBucket

router = APIRouter()

# Fixed bucket order for score_histogram
_SCORE_BUCKETS: list[tuple[str, float | None, float | None]] = [
    ("300-400", 300.0, 400.0),
    ("400-500", 400.0, 500.0),
    ("500-600", 500.0, 600.0),
    ("600-650", 600.0, 650.0),
    ("650-700", 650.0, 700.0),
    ("700-750", 700.0, 750.0),
    ("750-800", 750.0, 800.0),
    ("800-850", 800.0, 850.0),
    ("850-900", 850.0, 900.0),
    ("900+", 900.0, None),
]


def _assign_bucket(score: float) -> str | None:
    """Return the label of the bucket that contains `score`, or None if outside all buckets."""
    for label, low, high in _SCORE_BUCKETS:
        if high is None:
            if score >= low:
                return label
        else:
            if low <= score < high:
                return label
    return None


@router.get("/risk-distribution", response_model=RiskDistributionResponse)
async def get_risk_distribution(
    period_days: int = Query(30, ge=1),
    _current_user: LenderUser = Depends(require_officer),
    decisioning_db: AsyncSession = Depends(get_decisioning_db),
) -> RiskDistributionResponse:
    period_cutoff = datetime.now(UTC) - timedelta(days=period_days)
    ud = underwriting_decisions_table

    # -----------------------------------------------------------------------
    # by_tier — GROUP BY risk_tier, skip NULL tiers
    # -----------------------------------------------------------------------
    stmt_tiers = (
        select(
            ud.c.risk_tier,
            func.count().label("count"),
            func.coalesce(func.sum(ud.c.approved_amount), 0).label("total_amount"),
            func.coalesce(func.avg(ud.c.interest_rate), 0).label("avg_rate"),
            func.sum(
                case((ud.c.decision == "APPROVE", 1), else_=0)
            ).label("approve_count"),
        )
        .where(
            ud.c.created_at >= period_cutoff,
            ud.c.risk_tier.isnot(None),
        )
        .group_by(ud.c.risk_tier)
        .order_by(ud.c.risk_tier)
    )

    result_tiers = await decisioning_db.execute(stmt_tiers)
    tier_rows = result_tiers.fetchall()

    by_tier: list[RiskByTier] = []
    for row in tier_rows:
        tier_label: str = row.risk_tier
        count: int = int(row.count)
        total_amount: float = float(row.total_amount)
        avg_rate: float = float(row.avg_rate)
        approve_count: int = int(row.approve_count) if row.approve_count is not None else 0
        approval_rate: float = (approve_count / count * 100.0) if count > 0 else 0.0

        by_tier.append(
            RiskByTier(
                tier=tier_label,
                count=count,
                total_amount=total_amount,
                avg_rate=avg_rate,
                approval_rate=approval_rate,
            )
        )

    # -----------------------------------------------------------------------
    # score_histogram — fetch raw scores, bucket in Python
    # -----------------------------------------------------------------------
    stmt_scores = select(ud.c.risk_score).where(
        ud.c.created_at >= period_cutoff,
        ud.c.risk_score.isnot(None),
    )
    result_scores = await decisioning_db.execute(stmt_scores)
    score_rows = result_scores.fetchall()

    # Build count map keyed by bucket label
    bucket_counts: dict[str, int] = {label: 0 for label, _, _ in _SCORE_BUCKETS}
    for (score,) in score_rows:
        if score is not None:
            label = _assign_bucket(float(score))
            if label is not None:
                bucket_counts[label] += 1

    score_histogram: list[ScoreHistogramBucket] = [
        ScoreHistogramBucket(bucket=label, count=bucket_counts[label])
        for label, _, _ in _SCORE_BUCKETS
    ]

    return RiskDistributionResponse(
        by_tier=by_tier,
        score_histogram=score_histogram,
    )
