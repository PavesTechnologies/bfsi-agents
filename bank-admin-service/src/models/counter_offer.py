import uuid
import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import String, Numeric, DateTime, Text, ForeignKey, text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base


class CounterOfferStatus(str, Enum):
    DRAFT               = "DRAFT"
    PUBLISHED           = "PUBLISHED"
    APPLICANT_RESPONDED = "APPLICANT_RESPONDED"
    EXPIRED             = "EXPIRED"


class ApplicantDecision(str, Enum):
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"


class CounterOfferSession(Base):
    """One counter-offer session per COUNTER_OFFER decisioning result.

    generated_options is the immutable LLM snapshot.
    current_options is the live working copy (reflects bank edits and additions).
    """
    __tablename__ = "counter_offer_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Financial summary ──────────────────────────────────────────────────────
    original_request_dti: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    max_affordable_emi: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    monthly_income: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    existing_monthly_obligations: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    qualifying_cap: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    # ── LLM-generated text ─────────────────────────────────────────────────────
    counter_offer_logic: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)

    # ── Offer snapshots ────────────────────────────────────────────────────────
    generated_options: Mapped[list] = mapped_column(JSONB, nullable=False)
    current_options: Mapped[list] = mapped_column(JSONB, nullable=False)

    # ── Recommendation ─────────────────────────────────────────────────────────
    recommended_option_id: Mapped[str] = mapped_column(String(20), nullable=False)
    recommendation_rationale: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Lifecycle ──────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DRAFT", index=True)

    published_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("bank_users.id", ondelete="SET NULL"), nullable=True
    )
    published_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Applicant response ─────────────────────────────────────────────────────
    applicant_decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    accepted_option_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    applicant_responded_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Expiry ─────────────────────────────────────────────────────────────────
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # ── Relationships ──────────────────────────────────────────────────────────
    edit_logs: Mapped[list["CounterOfferEditLog"]] = relationship(
        "CounterOfferEditLog", back_populates="session", cascade="all, delete-orphan"
    )


class CounterOfferEditLog(Base):
    """Append-only audit row written on every bank employee field change.

    old_value / new_value are JSONB to accommodate any scalar or structured value.
    """
    __tablename__ = "counter_offer_edit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("counter_offer_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # NULL means the edit was to a session-level field (e.g. recommended_option_id)
    option_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    new_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    edited_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("bank_users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    edited_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    session: Mapped["CounterOfferSession"] = relationship("CounterOfferSession", back_populates="edit_logs")
