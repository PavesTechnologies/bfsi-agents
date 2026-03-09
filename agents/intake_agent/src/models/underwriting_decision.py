import uuid
import datetime
from typing import Optional
from sqlalchemy import String, Integer, Numeric, DateTime, Text, text, Float, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

class Base(DeclarativeBase):
    pass

class UnderwritingDecision(Base):
    __tablename__ = 'underwriting_decisions'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_tier: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    approved_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    interest_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tenure_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reasoning_steps: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    raw_decision_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
