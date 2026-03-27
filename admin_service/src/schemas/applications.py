from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Sub-models — Applicant profile
# ---------------------------------------------------------------------------

class AddressSchema(BaseModel):
    address_id: str
    address_type: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]
    housing_status: Optional[str]
    monthly_housing_payment: Optional[float]
    years_at_address: Optional[int]
    months_at_address: Optional[int]


class EmploymentSchema(BaseModel):
    employment_id: str
    employment_type: Optional[str]
    employment_status: Optional[str]
    employer_name: Optional[str]
    job_title: Optional[str]
    start_date: Optional[date]
    experience: Optional[int]
    self_employed_flag: Optional[bool]
    gross_monthly_income: Optional[float]


class IncomeSchema(BaseModel):
    income_id: str
    income_type: Optional[str]
    description: Optional[str]
    monthly_amount: Optional[float]
    income_frequency: Optional[str]


class AssetSchema(BaseModel):
    asset_id: str
    asset_type: Optional[str]
    institution_name: Optional[str]
    value: Optional[float]
    ownership_type: Optional[str]


class LiabilitySchema(BaseModel):
    liability_id: str
    liability_type: Optional[str]
    creditor_name: Optional[str]
    outstanding_balance: Optional[float]
    monthly_payment: Optional[float]
    months_remaining: Optional[int]
    delinquent_flag: Optional[bool]


class DocumentSchema(BaseModel):
    document_id: str
    document_type: Optional[str]
    file_name: Optional[str]
    mime_type: Optional[str]
    file_size: Optional[int]
    uploaded_at: Optional[datetime]
    is_low_quality: Optional[bool]


class ApplicantSchema(BaseModel):
    applicant_id: str
    application_id: str
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    suffix: Optional[str]
    date_of_birth: Optional[date]
    applicant_role: Optional[str]
    email: Optional[str]
    ssn_last4: Optional[str]
    phone_number: Optional[str]
    gender: Optional[str]
    citizenship_status: Optional[str]
    addresses: list[AddressSchema] = []
    employment: Optional[EmploymentSchema] = None
    incomes: list[IncomeSchema] = []
    assets: list[AssetSchema] = []
    liabilities: list[LiabilitySchema] = []


class LoanApplicationSchema(BaseModel):
    application_id: str
    loan_type: Optional[str]
    credit_type: Optional[str]
    loan_purpose: Optional[str]
    requested_amount: Optional[float]
    requested_term_months: Optional[int]
    preferred_payment_day: Optional[int]
    origination_channel: Optional[str]
    application_status: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Sub-models — KYC
# ---------------------------------------------------------------------------

class AmlCheckSchema(BaseModel):
    id: str
    ofac_match: Optional[bool]
    ofac_confidence: Optional[float]
    pep_match: Optional[bool]
    aml_score: Optional[float]
    flags: Optional[Any]


class IdentityCheckSchema(BaseModel):
    id: str
    final_status: Optional[str]
    aggregated_score: Optional[float]
    hard_fail_triggered: Optional[bool]
    ssn_valid: Optional[bool]
    name_ssn_match: Optional[bool]
    dob_ssn_match: Optional[bool]
    deceased_flag: Optional[bool]


class KycResultSchema(BaseModel):
    kyc_case_id: str
    applicant_id: str
    status: Optional[str]          # PENDING | PASSED | REVIEW | FAILED
    confidence_score: Optional[float]
    rules_version: Optional[str]
    created_at: Optional[datetime]
    completed_at: Optional[datetime]
    risk_decision: Optional[str]   # PASS | REVIEW | FAIL (from risk_decisions table)
    identity_check: Optional[IdentityCheckSchema] = None
    aml_check: Optional[AmlCheckSchema] = None


# ---------------------------------------------------------------------------
# Sub-models — Underwriting
# ---------------------------------------------------------------------------

class CounterOfferOptionSchema(BaseModel):
    offer_id: str
    principal_amount: float
    tenure_months: int
    interest_rate: float
    monthly_emi: float
    label: str


class UnderwritingResultSchema(BaseModel):
    id: str
    decision: Optional[str]          # APPROVE | COUNTER_OFFER | DECLINE
    risk_tier: Optional[str]
    risk_score: Optional[float]
    approved_amount: Optional[float]
    disbursement_amount: Optional[float]
    interest_rate: Optional[float]
    tenure_months: Optional[int]
    explanation: Optional[str]
    decline_reason: Optional[str]
    reasoning_steps: Optional[list[str]] = []
    counter_offer_options: Optional[list[CounterOfferOptionSchema]] = None
    created_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Sub-models — Disbursement
# ---------------------------------------------------------------------------

class DisbursementSchema(BaseModel):
    id: str
    transaction_id: Optional[str]
    status: Optional[str]
    disbursement_amount: Optional[float]
    monthly_emi: Optional[float]
    total_interest: Optional[float]
    total_repayment: Optional[float]
    transfer_timestamp: Optional[datetime]
    repayment_schedule: Optional[Any]
    created_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Sub-models — Human review
# ---------------------------------------------------------------------------

class HumanReviewDecisionSchema(BaseModel):
    id: str
    decision: str
    override_amount: Optional[float]
    override_rate: Optional[float]
    override_tenure: Optional[int]
    selected_offer_id: Optional[str]
    notes: Optional[str]
    reviewed_by: str       # user full_name
    created_at: datetime


class HumanReviewSummarySchema(BaseModel):
    queue_id: str
    status: str
    assigned_to: Optional[str]    # user full_name
    ai_decision: str
    ai_risk_tier: Optional[str]
    ai_risk_score: Optional[float]
    ai_suggested_amount: Optional[float]
    ai_suggested_rate: Optional[float]
    ai_suggested_tenure: Optional[int]
    ai_counter_options: Optional[Any]
    ai_reasoning: Optional[list[str]]
    ai_decline_reason: Optional[str]
    created_at: datetime
    assigned_at: Optional[datetime]
    decided_at: Optional[datetime]
    latest_decision: Optional[HumanReviewDecisionSchema] = None


# ---------------------------------------------------------------------------
# Top-level response schemas
# ---------------------------------------------------------------------------

class ApplicationSummarySchema(BaseModel):
    """Used in paginated list responses."""
    application_id: str
    applicant_name: str
    email: Optional[str]
    loan_type: Optional[str]
    requested_amount: Optional[float]
    application_status: Optional[str]
    ai_decision: Optional[str]
    risk_tier: Optional[str]
    risk_score: Optional[float]
    human_review_status: Optional[str]
    created_at: Optional[datetime]


class ApplicationDetailSchema(BaseModel):
    """Full detail for a single application."""
    application: LoanApplicationSchema
    applicant: Optional[ApplicantSchema]
    documents: list[DocumentSchema] = []
    kyc: Optional[KycResultSchema] = None
    underwriting: Optional[UnderwritingResultSchema] = None
    disbursement: Optional[DisbursementSchema] = None
    human_review: Optional[HumanReviewSummarySchema] = None


class PaginatedApplicationsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ApplicationSummarySchema]


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class TimelineEventSchema(BaseModel):
    timestamp: datetime
    event: str
    stage: str
    status: str
    message: str
