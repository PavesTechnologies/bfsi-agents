# src/models/human_review.py

import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Text, Enum, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from src.utils.migration_database import Base
from .enums import HumanReviewDecision


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    kyc_attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("kyc_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        nullable=False,
    )

    decision: Mapped[HumanReviewDecision] = mapped_column(
        Enum(HumanReviewDecision, name="human_review_decision_enum"),
        nullable=False,
    )

    reviewer_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # 🔗 Relationship back to KYC Attempt
    kyc_attempt = relationship(
        "KYCAttempt",
        back_populates="human_reviews",
        lazy="selectin",
    )