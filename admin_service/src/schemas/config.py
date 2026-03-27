from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Risk Tier Config
# ---------------------------------------------------------------------------

class RiskTierConfigSchema(BaseModel):
    id: str
    tier: str
    min_interest_rate: float
    max_interest_rate: float
    default_interest_rate: float
    max_loan_amount: float
    min_loan_amount: float
    min_credit_score: int
    max_dti_ratio: float
    is_active: bool
    effective_from: datetime
    created_by: Optional[str] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class UpdateRiskTierRequest(BaseModel):
    default_interest_rate: float
    min_interest_rate: float
    max_interest_rate: float
    max_loan_amount: float
    min_loan_amount: float
    min_credit_score: int
    max_dti_ratio: float
    effective_from: datetime
    notes: Optional[str] = None

    @field_validator("max_interest_rate")
    @classmethod
    def validate_rate_range(cls, v, info):
        data = info.data
        min_r = data.get("min_interest_rate")
        default_r = data.get("default_interest_rate")
        if min_r is not None and v < min_r:
            raise ValueError("max_interest_rate must be >= min_interest_rate")
        if default_r is not None and (default_r < min_r or default_r > v):
            raise ValueError("default_interest_rate must be between min and max")
        return v


class PaginatedRiskTierHistory(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RiskTierConfigSchema]


# ---------------------------------------------------------------------------
# Loan Policy
# ---------------------------------------------------------------------------

class LoanPolicySchema(BaseModel):
    id: str
    policy_key: str
    policy_value: Any
    description: str
    category: str
    is_active: bool
    effective_from: datetime
    created_by: Optional[str] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class UpdatePolicyRequest(BaseModel):
    policy_value: Any
    notes: Optional[str] = None
    effective_from: datetime


class PaginatedPolicyHistory(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[LoanPolicySchema]
