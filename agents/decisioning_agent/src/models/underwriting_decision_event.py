import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, String, Text, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.migration_database import Base


class UnderwritingDecisionEvent(Base):
    __tablename__ = "underwriting_decision_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    application_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    underwriting_decision_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    actor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
