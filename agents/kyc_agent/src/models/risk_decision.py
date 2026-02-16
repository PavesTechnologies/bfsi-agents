from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, DateTime, ForeignKey, text, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.utils.migration_database import Base
from .enums import FinalDecision


class RiskDecision(Base):
    __tablename__ = "risk_decisions"

    id = mapped_column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))

    kyc_attempt_id = mapped_column(
        UUID,
        ForeignKey("kyc_attempts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    final_status = mapped_column(
        Enum(FinalDecision, name="decision_enum"),
        nullable=False,
    )

    aggregated_score = mapped_column(Float)
    hard_fail_triggered = mapped_column(Boolean)

    decision_reason = mapped_column(Text)

    decision_rules_snapshot = mapped_column(JSONB)
    model_versions = mapped_column(JSONB)

    created_at = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    kyc_attempt = relationship("KYCAttempt", back_populates="risk_decision")
