import uuid
import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LoanTermOptionSchema(BaseModel):
    option_id: str
    label: str
    proposed_amount: float
    proposed_tenure_months: int
    proposed_interest_rate: float
    monthly_payment_emi: float
    disbursement_amount: float
    total_repayment: float
    affordability_headroom_pct: float
    is_recommended: bool
    feasible: bool
    justification: str


class CounterOfferSessionResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    original_request_dti: float
    max_affordable_emi: float
    monthly_income: float
    existing_monthly_obligations: float
    qualifying_cap: float
    counter_offer_logic: str
    confidence_score: float
    generated_options: List[LoanTermOptionSchema]
    current_options: List[LoanTermOptionSchema]
    recommended_option_id: str
    recommendation_rationale: str
    status: str
    published_by: Optional[uuid.UUID] = None
    published_at: Optional[datetime.datetime] = None
    applicant_decision: Optional[str] = None
    accepted_option_id: Optional[str] = None
    applicant_responded_at: Optional[datetime.datetime] = None
    expires_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class OfferOptionUpdateRequest(BaseModel):
    """PATCH body for editing an existing offer option.

    Only provided fields are applied. Derived fields (EMI, disbursement, total,
    headroom) are always recalculated server-side when any financial field changes.
    """
    proposed_amount: Optional[float] = Field(None, gt=0)
    proposed_tenure_months: Optional[int] = Field(None, gt=0)
    proposed_interest_rate: Optional[float] = Field(None, gt=0)
    justification: Optional[str] = None
    note: Optional[str] = Field(None, description="Reason for this edit — stored in audit log")


class OfferOptionCreateRequest(BaseModel):
    """POST body for a bank-created custom offer option."""
    label: str
    proposed_amount: float = Field(gt=0)
    proposed_tenure_months: int = Field(gt=0)
    proposed_interest_rate: float = Field(gt=0)
    justification: str


class RecommendRequest(BaseModel):
    option_id: str
    note: Optional[str] = None


class CounterOfferSessionCreateInternal(BaseModel):
    """Orchestrator callback payload when the decisioning agent returns COUNTER_OFFER."""
    external_application_id: str
    counter_offer_data: Dict[str, Any]


class EditLogEntryResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    option_id: Optional[str] = None
    field_name: str
    old_value: Any
    new_value: Any
    edited_by: Optional[uuid.UUID] = None
    note: Optional[str] = None
    edited_at: datetime.datetime

    model_config = {"from_attributes": True}
