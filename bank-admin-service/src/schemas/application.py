import datetime
from typing import Optional, Any
from pydantic import BaseModel


class ApplicationSummary(BaseModel):
    application_id: str
    decision: Optional[str] = None
    risk_tier: Optional[str] = None
    risk_score: Optional[float] = None
    approved_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ApplicationDetail(BaseModel):
    application_id: str
    decision: Optional[str] = None
    risk_tier: Optional[str] = None
    risk_score: Optional[float] = None
    approved_amount: Optional[float] = None
    disbursement_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    explanation: Optional[str] = None
    decline_reason: Optional[str] = None
    reasoning_steps: Optional[Any] = None
    counter_offer_data: Optional[Any] = None
    parallel_tasks_executed: Optional[Any] = None
    node_execution_times: Optional[Any] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    items: list[ApplicationSummary]
    total: int
    page: int
    page_size: int


class DashboardStats(BaseModel):
    total_applications: int
    total_approved: int
    total_declined: int
    total_counter_offer: int
    approval_rate: float
    avg_risk_score: Optional[float] = None
    pending_rule_approvals: int


class FunnelStats(BaseModel):
    stage: str
    count: int


class DailyVolume(BaseModel):
    date: str
    approved: int
    declined: int
    counter_offer: int
    total: int
