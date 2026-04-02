import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, String, Text, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.migration_database import Base


class UnderwritingHumanReview(Base):
    __tablename__ = "underwriting_human_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    application_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    underwriting_decision_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    reviewer_id: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    review_status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'REVIEW_COMPLETED'"))
    reason_keys: Mapped[dict] = mapped_column(JSONB, nullable=False)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_packet: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
