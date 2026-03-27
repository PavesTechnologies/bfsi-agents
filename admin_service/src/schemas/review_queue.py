from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ReviewQueueItemSchema(BaseModel):
    id: str
    application_id: str
    status: str
    assigned_to: Optional[str] = None
    assignee_name: Optional[str] = None
    ai_decision: str
    ai_risk_tier: Optional[str] = None
    ai_risk_score: Optional[float] = None
    ai_suggested_amount: Optional[float] = None
    ai_suggested_rate: Optional[float] = None
    ai_suggested_tenure: Optional[int] = None
    ai_counter_options: Optional[Any] = None
    ai_reasoning: Optional[Any] = None
    ai_decline_reason: Optional[str] = None
    created_at: datetime
    assigned_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None


class PaginatedReviewQueueResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ReviewQueueItemSchema]


class DecideRequest(BaseModel):
    decision: str  # APPROVED, REJECTED, OVERRIDDEN
    override_amount: Optional[float] = None
    override_rate: Optional[float] = None
    override_tenure: Optional[int] = None
    selected_offer_id: Optional[str] = None
    notes: Optional[str] = None


class DecideResponse(BaseModel):
    queue_id: str
    decision: str
    status: str
    orchestrator_notified: bool
