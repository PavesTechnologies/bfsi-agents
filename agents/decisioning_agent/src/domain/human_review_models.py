"""Domain models for underwriting human review operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UnderwritingHumanReviewRequest(BaseModel):
    application_id: str
    reviewer_id: str
    decision: str = Field(description="One of: APPROVE, REJECT, RETURNED_FOR_DATA")
    reason_keys: List[str]
    comments: Optional[str] = None
    review_packet: Optional[Dict[str, Any]] = None


class UnderwritingHumanReviewResponse(BaseModel):
    application_id: str
    underwriting_decision_id: Optional[str] = None
    reviewer_id: str
    decision: str
    review_status: str
    reason_keys: List[str]
    comments: Optional[str] = None
    created_at: datetime


class UnderwritingHumanReviewSummary(BaseModel):
    application_id: str
    latest_review: Optional[UnderwritingHumanReviewResponse] = None
