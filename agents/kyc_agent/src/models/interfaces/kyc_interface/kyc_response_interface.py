from uuid import UUID

from pydantic import BaseModel


class KYCTriggerResponse(BaseModel):
    attempt_id: UUID
    kyc_status: str
