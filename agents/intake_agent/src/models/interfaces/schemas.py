from pydantic import BaseModel, AnyUrl
from uuid import UUID


class IntakeRequest(BaseModel):
    request_id: UUID
    app_id: UUID
    payload: dict
    callback_url: AnyUrl
