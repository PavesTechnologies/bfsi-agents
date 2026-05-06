import uuid
import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role_id: int


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: RoleOut
    is_active: bool
    created_at: datetime.datetime
    last_login_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int
