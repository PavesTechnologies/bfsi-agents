import uuid
import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import String, Boolean, Numeric, Integer, DateTime, Text, ForeignKey, text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base


class PipelineStatus(str, Enum):
    RECEIVED                    = "RECEIVED"
    KYC_IN_PROGRESS             = "KYC_IN_PROGRESS"
    KYC_FAILED                  = "KYC_FAILED"
    AWAITING_BANK_REVIEW        = "AWAITING_BANK_REVIEW"
    DECISIONING_IN_PROGRESS     = "DECISIONING_IN_PROGRESS"
    AWAITING_BANK_APPROVAL      = "AWAITING_BANK_APPROVAL"
    BANK_DECLINED               = "BANK_DECLINED"
    AWAITING_APPLICANT_RESPONSE = "AWAITING_APPLICANT_RESPONSE"
    AWAITING_SIGNATURE          = "AWAITING_SIGNATURE"
    SIGNATURE_COMPLETE          = "SIGNATURE_COMPLETE"
    DISBURSEMENT_IN_PROGRESS    = "DISBURSEMENT_IN_PROGRESS"
    DISBURSED                   = "DISBURSED"
    CANCELLED                   = "CANCELLED"


class LoanApplication(Base):
    """Full pipeline state for a loan application — source of truth for the HITL workflow."""
    __tablename__ = "loan_applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    external_application_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    pipeline_status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=PipelineStatus.RECEIVED, index=True)

    applicant_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    loan_amount_requested: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    loan_tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    loan_purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    kyc_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    kyc_result_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    kyc_completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    active_analyzers: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    analyzers_selected_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("bank_users.id", ondelete="SET NULL"), nullable=True)
    analyzers_selected_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    decisioning_result_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    llm_decision: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    llm_risk_tier: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    llm_risk_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    llm_approved_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    llm_interest_rate: Mapped[Optional[float]] = mapped_column(Numeric(6, 4), nullable=True)
    llm_tenure_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    llm_counter_offer_options: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    decisioning_completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    bank_final_decision: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    bank_approved_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    bank_interest_rate: Mapped[Optional[float]] = mapped_column(Numeric(6, 4), nullable=True)
    bank_tenure_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bank_override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bank_decided_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("bank_users.id", ondelete="SET NULL"), nullable=True)
    bank_decided_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    applicant_accepted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    applicant_responded_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    loan_document_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    loan_document_generated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    signature_full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    signature_agreed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    signature_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    signature_user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    disbursement_transaction_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    disbursed_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    disbursed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    disbursement_receipt_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
