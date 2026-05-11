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
    # CREATE | UPDATE | DELETE — derived from old_value / new_value pattern.
    action_type: str = "UPDATE"
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
    category_name: Optional[str] = None
    risk_level: Optional[str] = None
    # CREATE | UPDATE | DELETE (derived from history shape).
    action_type: str = "UPDATE"
    # Back-compat — UI versions before action_type was wired still read this.
    is_create: bool = False
    old_value: Optional[dict] = None
    new_value: dict
    changed_by: uuid.UUID
    changed_by_name: Optional[str] = None
    change_reason: Optional[str] = None
    created_at: datetime.datetime


class ApprovalActionRequest(BaseModel):
    comment: Optional[str] = None


class RuleCreateRequest(BaseModel):
    category_id: int
    rule_key: str
    display_name: str
    description: Optional[str] = None
    current_value: dict  # JSON value, e.g. {"value": 750} or {"value": [...]}
    default_value: Optional[dict] = None  # falls back to current_value
    data_type: str  # number | boolean | string | json
    validation_schema: Optional[dict] = None
    risk_level: str = "low"  # low | high
    # NOTE: ignored server-side. Every rule create goes through the HITL
    # approval queue. Field is kept for back-compat with older UI builds.
    requires_approval: bool = True
    change_reason: str


class RuleDeleteRequest(BaseModel):
    change_reason: str
