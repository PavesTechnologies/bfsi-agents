"""
Domain models for the underwriting API.

These models define the canonical response contract consumed by the
disbursement agent and the orchestrator.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# Anchors of the deterministic decision math. Must be present whenever the
# caller passes an explicit `active_analyzers` list.
_MANDATORY_ANALYZERS: frozenset[str] = frozenset({"credit_score", "public_record", "income"})


class UnderwritingRequest(BaseModel):
    """Input payload for the underwriting decision pipeline."""
    application_id: str = Field(description="Unique loan application identifier")
    raw_experian_data: Dict[str, Any] = Field(description="Full Experian credit report JSON")
    requested_amount: float = Field(description="Loan amount requested by the applicant", gt=0)
    requested_tenure_months: int = Field(description="Requested loan tenure in months", gt=0)
    monthly_income: float = Field(description="Applicant's gross monthly income", ge=0)


class CIBILUnderwritingRequest(BaseModel):
    """Input payload for the post-KYC CIBIL decisioning pipeline (Indian bureau)."""
    application_id: str = Field(description="Unique loan application ID", example="APP-IND-2026-001")
    pan: str = Field(description="Verified PAN number from KYC agent (10 chars)", example="ABCDE0001F")
    full_name: str = Field(description="Applicant full name", example="Ravi Kumar")
    requested_amount: float = Field(description="Requested loan amount in INR", gt=0, example=500000)
    requested_tenure_months: int = Field(description="Requested tenure in months", gt=0, example=36)
    monthly_income: float = Field(description="Gross monthly income in INR from bank statement", ge=0, example=75000)


# ─────────────────────────────────────────────────────────────────────────────
# Indian (RAG-augmented) request schema
# ─────────────────────────────────────────────────────────────────────────────


class IndianApplicantAddress(BaseModel):
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    pincode: str


class IndianApplicantData(BaseModel):
    full_name: str
    dob: str = Field(description="YYYY-MM-DD")
    aadhaar_number: str
    pan_number: str
    phone: str
    email: str
    address: IndianApplicantAddress


class IndianLoanRequest(BaseModel):
    """Optional loan-request block. If omitted the service falls back to defaults."""
    amount: float = Field(gt=0, description="Loan amount in INR")
    tenure_months: int = Field(gt=0, description="Tenure in months")


class IndianUnderwritingRequest(BaseModel):
    """
    Request for the RAG-augmented Indian underwriting pipeline.

    The pipeline pulls the CIBIL report from MockCIBILAdapter using
    `applicant_data.pan_number`, fetches RBI / bank policy context from
    Qdrant, and runs the same 7-analyzer graph the existing /underwrite/cibil
    endpoint uses — with an extra `rag_retrieval` node injected before the
    fan-out and `{rag_context}` woven into every analyzer prompt.

    `loan_request` and `monthly_income` are optional. When omitted they
    default to typical retail-loan values (₹5L / 36mo / ₹50k) so the
    decision and counter-offer LLM nodes can still produce structured output
    in their existing parser shapes.
    """
    application_id: str = Field(example="3fa85f64-5717-4562-b3fc-2c963f66afa6")
    applicant_data: IndianApplicantData
    loan_request: Optional[IndianLoanRequest] = Field(
        default=None,
        description="Optional. Defaults to amount=500000 INR, tenure_months=36.",
    )
    monthly_income: Optional[float] = Field(
        default=None,
        ge=0,
        description="Optional gross monthly income (INR). Defaults to 50000.",
    )
    active_analyzers: Optional[List[str]] = Field(
        default=None,
        description=(
            "Subset of analyzers to run. None means run all. "
            "Valid keys: credit_score, public_record, utilization, "
            "exposure, behavior, inquiry, income. "
            "credit_score, public_record, and income are mandatory when "
            "the list is provided."
        ),
    )

    @field_validator("active_analyzers")
    @classmethod
    def _enforce_mandatory(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        missing = _MANDATORY_ANALYZERS - set(v)
        if missing:
            raise ValueError(
                f"Mandatory analyzers cannot be deselected: {sorted(missing)}"
            )
        return v


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


class UnderwritingResponse(BaseModel):
    """Output payload returned by the underwriting decision pipeline."""
    application_id: str
    correlation_id: Optional[str] = None
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

    # DECLINE path
    decline_reason: Optional[str] = None
    reasoning_steps: Optional[List[str]] = None
