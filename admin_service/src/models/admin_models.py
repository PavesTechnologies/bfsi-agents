import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from src.db.base import Base


class LenderUser(Base):
    __tablename__ = "lender_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'OFFICER' | 'MANAGER' | 'ADMIN'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=datetime.utcnow,
        nullable=False,
    )

    review_queue_assignments: Mapped[list["HumanReviewQueue"]] = relationship(
        "HumanReviewQueue",
        foreign_keys="HumanReviewQueue.assigned_to",
        back_populates="assignee",
        lazy="noload",
    )
    review_decisions: Mapped[list["HumanReviewDecision"]] = relationship(
        "HumanReviewDecision",
        foreign_keys="HumanReviewDecision.reviewed_by",
        back_populates="reviewer",
        lazy="noload",
    )


class HumanReviewQueue(Base):
    __tablename__ = "human_review_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    application_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )  # PENDING | IN_REVIEW | APPROVED | REJECTED | OVERRIDDEN
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lender_users.id", ondelete="SET NULL"), nullable=True
    )

    # AI recommendation snapshot (stored when queue entry is created)
    ai_decision: Mapped[str] = mapped_column(String(20), nullable=False)
    ai_risk_tier: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    ai_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_suggested_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_suggested_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_suggested_tenure: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_counter_options: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ai_reasoning: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    ai_decline_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    assignee: Mapped[Optional["LenderUser"]] = relationship(
        "LenderUser",
        foreign_keys=[assigned_to],
        back_populates="review_queue_assignments",
        lazy="noload",
    )
    decisions: Mapped[list["HumanReviewDecision"]] = relationship(
        "HumanReviewDecision",
        back_populates="queue_entry",
        lazy="noload",
    )


class HumanReviewDecision(Base):
    __tablename__ = "human_review_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    queue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("human_review_queue.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reviewed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lender_users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    decision: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # APPROVED | REJECTED | APPROVED_WITH_OVERRIDE

    override_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    override_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    override_tenure: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    selected_offer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    queue_entry: Mapped["HumanReviewQueue"] = relationship(
        "HumanReviewQueue", back_populates="decisions", lazy="noload"
    )
    reviewer: Mapped["LenderUser"] = relationship(
        "LenderUser",
        foreign_keys=[reviewed_by],
        back_populates="review_decisions",
        lazy="noload",
    )


class RiskTierConfig(Base):
    """Append-only versioned interest rate configuration per risk tier."""

    __tablename__ = "risk_tier_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    tier: Mapped[str] = mapped_column(String(5), nullable=False, index=True)  # A | B | C | F
    min_interest_rate: Mapped[float] = mapped_column(Float, nullable=False)
    max_interest_rate: Mapped[float] = mapped_column(Float, nullable=False)
    default_interest_rate: Mapped[float] = mapped_column(Float, nullable=False)
    max_loan_amount: Mapped[float] = mapped_column(Float, nullable=False)
    min_loan_amount: Mapped[float] = mapped_column(Float, nullable=False)
    min_credit_score: Mapped[int] = mapped_column(Integer, nullable=False)
    max_dti_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lender_users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class LoanPolicy(Base):
    """Append-only versioned loan policy key-value store."""

    __tablename__ = "loan_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    policy_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    policy_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # LIMITS | UNDERWRITING | DISBURSEMENT | KYC
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lender_users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
