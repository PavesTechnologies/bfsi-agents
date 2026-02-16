
from pydantic import BaseModel
from uuid import UUID


class KYCTriggerResponse(BaseModel):
    attempt_id: UUID
    kyc_status: str
