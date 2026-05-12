import uuid
import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, field_validator


# Anchors of the deterministic decision math. The UI locks these checkboxes;
# this validator enforces the same rule server-side for direct API callers.
_MANDATORY_ANALYZERS: frozenset[str] = frozenset({"credit_score", "public_record", "income"})


class LoanApplicationCreate(BaseModel):
    external_application_id: str
    kyc_status: str
    kyc_result_snapshot: dict
    applicant_snapshot: dict
    loan_amount_requested: float
    loan_tenure_months: int
    loan_purpose: Optional[str] = None


class AnalyzerSelectionRequest(BaseModel):
    active_analyzers: Optional[List[str]] = None

    @field_validator("active_analyzers")
    @classmethod
    def _enforce_mandatory(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        # `None` means "run all analyzers" — that's fine. A concrete list must
        # always include credit_score, public_record, and income.
        if v is None:
            return v
        missing = _MANDATORY_ANALYZERS - set(v)
        if missing:
            raise ValueError(
                f"Mandatory analyzers cannot be deselected: {sorted(missing)}"
            )
        return v


class BankDecisionRequest(BaseModel):
    final_decision: str  # APPROVE | DECLINE
    approved_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    override_reason: Optional[str] = None


class DecisioningResultPatch(BaseModel):
    llm_decision: str
    llm_risk_tier: Optional[str] = None
    llm_risk_score: Optional[float] = None
    llm_approved_amount: Optional[float] = None
    llm_interest_rate: Optional[float] = None
    llm_tenure_months: Optional[int] = None
    llm_counter_offer_options: Optional[List[Any]] = None
    decisioning_result_snapshot: Optional[dict] = None


class SignaturePatch(BaseModel):
    full_name: str
    agreed: bool
    ip: Optional[str] = None
    user_agent: Optional[str] = None


class DisbursementPatch(BaseModel):
    transaction_id: str
    disbursed_amount: float
    disbursement_receipt_snapshot: dict


class LoanApplicationSummary(BaseModel):
    id: uuid.UUID
    external_application_id: str
    pipeline_status: str
    loan_amount_requested: float
    loan_tenure_months: int
    loan_purpose: Optional[str] = None
    kyc_status: Optional[str] = None
    llm_decision: Optional[str] = None
    llm_risk_tier: Optional[str] = None
    llm_risk_score: Optional[float] = None
    llm_approved_amount: Optional[float] = None
    llm_interest_rate: Optional[float] = None
    llm_tenure_months: Optional[int] = None
    bank_final_decision: Optional[str] = None
    bank_approved_amount: Optional[float] = None
    bank_interest_rate: Optional[float] = None
    bank_tenure_months: Optional[int] = None
    bank_decided_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class LoanApplicationDetail(LoanApplicationSummary):
    """Full detail view — inherits all summary fields and adds the heavy snapshots."""
    applicant_snapshot: dict

    kyc_result_snapshot: Optional[dict] = None
    kyc_completed_at: Optional[datetime.datetime] = None

    active_analyzers: Optional[List[str]] = None
    analyzers_selected_at: Optional[datetime.datetime] = None

    decisioning_result_snapshot: Optional[dict] = None
    llm_counter_offer_options: Optional[List[Any]] = None
    decisioning_completed_at: Optional[datetime.datetime] = None

    bank_override_reason: Optional[str] = None

    applicant_accepted: Optional[bool] = None
    signed_at: Optional[datetime.datetime] = None

    disbursement_transaction_id: Optional[str] = None
    disbursed_amount: Optional[float] = None
    disbursed_at: Optional[datetime.datetime] = None


class LoanApplicationListResponse(BaseModel):
    items: List[LoanApplicationSummary]
    total: int
    page: int
    page_size: int
