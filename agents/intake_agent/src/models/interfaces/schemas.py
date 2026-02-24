from uuid import UUID

from pydantic import AnyUrl, BaseModel


class IntakeRequest(BaseModel):
    request_id: UUID
    app_id: UUID
    payload: dict
    callback_url: AnyUrl
