from pydantic import BaseModel
from typing import Optional, List
from src.models.enums import ApplicantStatus, HumanDecision
from datetime import datetime

class HumanInLoopRequest(BaseModel):
    application_id: str
    reviewer_id: str
    decision: HumanDecision
    reason_codes: List[str]
    comments: Optional[str] = None
    
class HumanInLoopResponse(BaseModel):
    application_id: str
    response: str
    
    
class HumanReviewSummary(BaseModel):
    reviewer_id: str
    decision: HumanDecision
    reason_codes: List[str]
    comments: Optional[str]
    created_at: datetime
    
class GetApplicationResponse(BaseModel):
    application_id: str
    application_status: ApplicantStatus
    latest_human_review: Optional[HumanReviewSummary]