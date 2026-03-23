import uuid
import datetime
from typing import Optional
from sqlalchemy import String, Integer, Numeric, DateTime, Text, text, Float, Uuid, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.utils.migration_database import Base

class UnderwritingDecision(Base):
    __tablename__ = 'underwriting_decisions'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)  # APPROVE, DECLINE, COUNTER_OFFER
    risk_tier: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # --- Approved Loan Details ---
    approved_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    disbursement_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)  # After deducting origination fee
    interest_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tenure_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # --- Decision Details ---
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decline_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For DECLINE decisions
    reasoning_steps: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # --- Counter Offer (when decision = COUNTER_OFFER) ---
    counter_offer_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # --- Audit & Performance Tracking ---
    thread_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # For workflow resumption tracking
    execution_time_ms: Mapped[Optional[BigInteger]] = mapped_column(BigInteger, nullable=True)
    parallel_tasks_executed: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # List of executed nodes
    node_execution_times: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Performance metrics per node
    
    # --- Full Audit Trail ---
    raw_decision_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))
