import uuid
import datetime
from typing import Optional
from pydantic import BaseModel
from src.schemas.rule import RuleOut


class UserRuleOverrideCreate(BaseModel):
    override_value: dict
    override_reason: Optional[str] = None


class UserRuleOverrideOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    rule_id: uuid.UUID
    override_value: dict
    override_reason: Optional[str] = None
    created_by: uuid.UUID
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class UserRuleWithOverride(RuleOut):
    """A bank rule enriched with the user-specific override (if any)."""
    is_overridden: bool = False
    override_value: Optional[dict] = None
    override_reason: Optional[str] = None
    effective_value: dict  # override_value if overridden, else current_value
