from datetime import datetime

from pydantic import BaseModel
from src.models.enums import ApplicantStatus, HumanDecision


class HumanInLoopRequest(BaseModel):
    application_id: str
    reviewer_id: str
    decision: HumanDecision
    reason_codes: list[str]
    comments: str | None = None


class HumanInLoopResponse(BaseModel):
    application_id: str
    response: str


class HumanReviewSummary(BaseModel):
    reviewer_id: str
    decision: HumanDecision
    reason_codes: list[str]
    comments: str | None
    created_at: datetime


class GetApplicationResponse(BaseModel):
    application_id: str
    application_status: ApplicantStatus
    latest_human_review: HumanReviewSummary | None
