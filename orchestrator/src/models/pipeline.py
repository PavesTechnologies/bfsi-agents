"""Pipeline request and response models."""

from typing import Any, Dict

from pydantic import BaseModel, Field


class ApplicationTriggerRequest(BaseModel):
    application_id: str
    raw_application: Dict[str, Any]


class CounterOfferOption(BaseModel):
    offer_id: str
    principal_amount: float
    tenure_months: int
    interest_rate: float
    monthly_emi: float
    label: str


class ResumeWithOfferRequest(BaseModel):
    application_id: str
    selected_offer_id: str


class ConfirmApprovalRequest(BaseModel):
    application_id: str
    accepted: bool = Field(description="Must be true to proceed with disbursement")
