from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class CallbackStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class CallbackPayload(BaseModel):
    request_id: str
    status: str  # SUCCESS | FAILURE
    timestamp: datetime
    data: dict | None = None
    error: str | None = None
