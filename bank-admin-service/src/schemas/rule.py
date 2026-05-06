import uuid
import datetime
from typing import Optional, Any
from pydantic import BaseModel


class RuleCategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class RuleOut(BaseModel):
    id: uuid.UUID
    category: RuleCategoryOut
    rule_key: str
    display_name: str
    description: Optional[str] = None
    current_value: dict
    default_value: dict
    data_type: str
    validation_schema: Optional[dict] = None
    risk_level: str
    requires_approval: bool
    is_active: bool
    version: int
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class RuleListResponse(BaseModel):
    items: list[RuleOut]
    total: int


class RulePatchRequest(BaseModel):
    new_value: dict
    change_reason: str


class RuleHistoryOut(BaseModel):
    id: uuid.UUID
    rule_id: uuid.UUID
    version: int
    old_value: Optional[dict] = None
    new_value: dict
    changed_by: uuid.UUID
    changed_by_name: Optional[str] = None
    change_reason: Optional[str] = None
    approval_status: str
    reviewer_comment: Optional[str] = None
    created_at: datetime.datetime
    reviewed_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


class PendingApprovalOut(BaseModel):
    id: uuid.UUID
    rule_id: uuid.UUID
    rule_key: str
    rule_display_name: str
    old_value: Optional[dict] = None
    new_value: dict
    changed_by: uuid.UUID
    changed_by_name: Optional[str] = None
    change_reason: Optional[str] = None
    created_at: datetime.datetime


class ApprovalActionRequest(BaseModel):
    comment: Optional[str] = None
