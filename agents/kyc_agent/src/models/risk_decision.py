# src/models/risk_decision.py

import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, DateTime, ForeignKey, text, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.utils.migration_database import Base
from .enums import FinalDecision
from .kyc_cases import KYC

class RiskDecision(Base):
    __tablename__ = "risk_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    kyc_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("kyc_cases.id", ondelete="CASCADE"),
        unique=True,   # 1:1 relationship
        nullable=False,
        index=True,
    )

    final_status: Mapped[FinalDecision] = mapped_column(
        Enum(FinalDecision, name="decision_enum"),
        nullable=False,
        index=True,
    )

    aggregated_score: Mapped[float | None] = mapped_column(Float)

    hard_fail_triggered: Mapped[bool | None] = mapped_column(Boolean)

    decision_reason: Mapped[str | None] = mapped_column(Text)

    decision_rules_snapshot: Mapped[dict | None] = mapped_column(JSONB)

    model_versions: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
        index=True,
    )

    # 🔗 Relationship
    kyc: Mapped["KYC"] = relationship(
        "KYC",
        back_populates="risk_decision"
    )
