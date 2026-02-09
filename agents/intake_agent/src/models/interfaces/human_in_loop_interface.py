from pydantic import BaseModel
from typing import Optional, List
from src.models.enums import HumanDecision

class HumanInLoopRequest(BaseModel):
    application_id: str
    reviewer_id: str
    decision: HumanDecision
    reason_codes: List[str]
    comments: Optional[str] = None
    
class HumanInLoopResponse(BaseModel):
    application_id: str
    response: str