"""
Domain models for the underwriting API.

These models define the canonical response contract consumed by the
disbursement agent and the orchestrator.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UnderwritingRequest(BaseModel):
    """Input payload for the underwriting decision pipeline."""
    application_id: str = Field(description="Unique loan application identifier")
    raw_experian_data: Dict[str, Any] = Field(description="Full Experian credit report JSON")
    requested_amount: float = Field(description="Loan amount requested by the applicant", gt=0)
    requested_tenure_months: int = Field(description="Requested loan tenure in months", gt=0)
    monthly_income: float = Field(description="Applicant's gross monthly income", ge=0)


class LoanDetails(BaseModel):
    approved_amount: float
    approved_tenure_months: int
    interest_rate: float
    disbursement_amount: float
    explanation: str


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


class CounterOfferDetails(BaseModel):
    original_request_dti: float
    max_affordable_emi: float
    counter_offer_logic: str
    generated_options: List[LoanTermOption]
    confidence_score: float
    timestamp: Optional[str] = None


class ReviewPacket(BaseModel):
    application_id: str
    recommended_action: str
    summary: Optional[str] = None
    requested_amount: float
    requested_tenure_months: int
    risk_tier: Optional[str] = None
    risk_score: Optional[float] = None
    key_factors: List[str]
    reasoning_steps: List[str]
    suggested_reason_keys: List[str]
    candidate_reason_codes: Optional[List[Dict[str, Any]]] = None
    policy_citations: Optional[List[Dict[str, Any]]] = None
    feature_attribution_summary: Optional[Dict[str, Any]] = None
    metrics: Dict[str, Any]
    audit_summary: Optional[Dict[str, Any]] = None


class UnderwritingResponse(BaseModel):
    """Output payload returned by the underwriting decision pipeline."""
    application_id: str
    correlation_id: Optional[str] = None
    policy_version: Optional[str] = None
    audit_summary: Optional[Dict[str, Any]] = None
    decision: str = Field(description="APPROVE, COUNTER_OFFER, or DECLINE")
    risk_tier: Optional[str] = Field(default=None, description="Aggregated risk tier: A, B, C, F")
    risk_score: Optional[float] = Field(default=None, description="Aggregated risk score")
    timestamp: Optional[str] = None

    # APPROVE path
    loan_details: Optional[LoanDetails] = Field(
        default=None,
        description="Approved loan details: amount, tenure, rate, disbursement"
    )

    # COUNTER_OFFER path
    counter_offer: Optional[CounterOfferDetails] = Field(
        default=None,
        description="Counter offer data with alternative options"
    )
    original_decision_explanation: Optional[str] = None
    review_packet: Optional[ReviewPacket] = None

    # DECLINE path
    decline_reason: Optional[str] = None
    primary_reason_key: Optional[str] = None
    secondary_reason_key: Optional[str] = None
    adverse_action_reasons: Optional[List[Dict[str, str]]] = None
    adverse_action_notice: Optional[str] = None
    reasoning_summary: Optional[str] = None
    key_factors: Optional[List[str]] = None
    reasoning_steps: Optional[List[str]] = None
    candidate_reason_codes: Optional[List[Dict[str, Any]]] = None
    selected_reason_codes: Optional[List[Dict[str, Any]]] = None
    policy_citations: Optional[List[Dict[str, Any]]] = None
    retrieval_evidence: Optional[List[Dict[str, Any]]] = None
    feature_attribution_summary: Optional[Dict[str, Any]] = None
    explanation_generation_mode: Optional[str] = None
    critic_failures: Optional[List[str]] = None
