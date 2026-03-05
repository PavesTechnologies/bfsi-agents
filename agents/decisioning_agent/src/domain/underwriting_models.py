"""
Domain Models for the Underwriting API.

Pydantic models representing the HTTP contract for the /underwrite endpoint.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class UnderwritingRequest(BaseModel):
    """Input payload for the underwriting decision pipeline."""
    application_id: str = Field(description="Unique loan application identifier")
    raw_experian_data: Dict[str, Any] = Field(description="Full Experian credit report JSON")
    requested_amount: float = Field(description="Loan amount requested by the applicant", gt=0)
    requested_tenure_months: int = Field(description="Requested loan tenure in months", gt=0)
    monthly_income: float = Field(description="Applicant's gross monthly income", ge=0)


class LoanTermOption(BaseModel):
    """A single counter-offer restructuring option."""
    option_id: str
    description: str
    proposed_amount: float
    proposed_tenure_months: int
    proposed_interest_rate: float
    disbursement_amount: float
    monthly_payment_emi: float
    total_repayment: float


class UnderwritingResponse(BaseModel):
    """Output payload returned by the underwriting decision pipeline."""
    application_id: str
    decision: str = Field(description="APPROVE, COUNTER_OFFER, or DECLINE")
    aggregated_risk_tier: Optional[str] = Field(default=None, description="Aggregated risk tier: A, B, C, F")
    aggregated_risk_score: Optional[float] = Field(default=None, description="Aggregated risk score")
    timestamp: Optional[str] = None

    # APPROVE path
    loan_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Approved loan details: amount, tenure, rate, disbursement"
    )

    # COUNTER_OFFER path
    counter_offer: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Counter offer data with alternative options"
    )
    original_decision_explanation: Optional[str] = None

    # DECLINE path
    decline_reason: Optional[str] = None
    reasoning_steps: Optional[List[str]] = None
