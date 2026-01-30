from enum import Enum
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional


class CallbackStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class CallbackPayload(BaseModel):
    request_id: str
    status: str  # SUCCESS | FAILURE
    timestamp: datetime
    data: Optional[dict] = None
    error: Optional[str] = None