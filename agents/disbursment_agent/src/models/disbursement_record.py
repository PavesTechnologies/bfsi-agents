import uuid
import datetime
from typing import Optional
from sqlalchemy import String, Integer, Numeric, DateTime, text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.utils.migration_database import Base

class DisbursementRecord(Base):
    __tablename__ = 'disbursement_records'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    disbursement_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    transfer_timestamp: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    monthly_emi: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    total_interest: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    total_repayment: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    repayment_schedule: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    receipt_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
