from enum import StrEnum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CallbackStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class CallbackPayload(BaseModel):
    request_id: str
    status: str  # SUCCESS | FAILURE
    timestamp: datetime
    data: Optional[dict] = None
    error: Optional[str] = None
