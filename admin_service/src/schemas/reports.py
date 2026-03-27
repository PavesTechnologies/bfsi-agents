"""Response schemas for Phase 5 — Reporting & Analytics endpoints."""
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# GET /reports/dashboard
# ---------------------------------------------------------------------------

class DashboardResponse(BaseModel):
    total_applications: int
    pending_review: int
    in_review: int
    approved_today: int
    rejected_today: int
    total_disbursed_amount: float
    avg_risk_score: float
    approval_rate_percent: float
    avg_loan_amount: float
    avg_processing_time_hours: float


# ---------------------------------------------------------------------------
# GET /reports/applications
# ---------------------------------------------------------------------------

class ApplicationChartPoint(BaseModel):
    date: str
    total: int
    approved: int
    declined: int
    counter_offer: int
    pending: int


class ApplicationsSummary(BaseModel):
    total: int
    approved: int
    declined: int
    counter_offer: int
    pending_human_review: int
    human_rejected: int


class ApplicationsReportResponse(BaseModel):
    chart_data: list[ApplicationChartPoint]
    summary: ApplicationsSummary


# ---------------------------------------------------------------------------
# GET /reports/risk-distribution
# ---------------------------------------------------------------------------

class RiskByTier(BaseModel):
    tier: str
    count: int
    total_amount: float
    avg_rate: float
    approval_rate: float


class ScoreHistogramBucket(BaseModel):
    bucket: str
    count: int


class RiskDistributionResponse(BaseModel):
    by_tier: list[RiskByTier]
    score_histogram: list[ScoreHistogramBucket]


# ---------------------------------------------------------------------------
# GET /reports/disbursements
# ---------------------------------------------------------------------------

class DisbursementChartPoint(BaseModel):
    date: str
    count: int
    total_amount: float
    avg_amount: float


class DisbursementsSummary(BaseModel):
    total_count: int
    total_amount: float
    avg_loan_amount: float
    avg_interest_rate: float
    avg_tenure_months: float
    total_interest_income: float


class DisbursementsReportResponse(BaseModel):
    chart_data: list[DisbursementChartPoint]
    summary: DisbursementsSummary


# ---------------------------------------------------------------------------
# GET /reports/review-performance
# ---------------------------------------------------------------------------

class OfficerPerformance(BaseModel):
    officer_id: str
    officer_name: str
    reviewed_count: int
    avg_review_time_hours: float
    approved: int
    rejected: int
    overridden: int


class ReviewPerformanceResponse(BaseModel):
    by_officer: list[OfficerPerformance]
    override_rate_percent: float
    ai_agreement_rate: float
