import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, String, Text, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.migration_database import Base


class UnderwritingMonitoringSnapshot(Base):
    __tablename__ = "underwriting_monitoring_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    segment_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    generated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    thresholds: Mapped[dict] = mapped_column(JSONB, nullable=False)
    report: Mapped[dict] = mapped_column(JSONB, nullable=False)
    alerts: Mapped[dict] = mapped_column(JSONB, nullable=False)
    baseline_records: Mapped[dict] = mapped_column(JSONB, nullable=False)
    current_records: Mapped[dict] = mapped_column(JSONB, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
