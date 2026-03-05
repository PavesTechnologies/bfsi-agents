from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    String, Text, DateTime, Enum,
    ForeignKeyConstraint, PrimaryKeyConstraint, text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid
import datetime
from src.utils.migration_database import Base 
from .enums import HumanDecision

class HumanReview(Base):
    __tablename__ = "human_review"
    __table_args__ = (
        ForeignKeyConstraint(
            ["application_id"],
            ["loan_application.application_id"],
            ondelete="CASCADE",
            name="fk_human_review_application",
        ),
        PrimaryKeyConstraint("id", name="human_review_pkey"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        nullable=False,
    )

    reviewer_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    decision: Mapped[HumanDecision] = mapped_column(
        Enum(HumanDecision, name="human_decision_enum"),
        nullable=False,
    )

    reason_codes: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # 🔗 back-reference, again by STRING
    application = relationship(
        "LoanApplication",
        back_populates="human_reviews",
        lazy="selectin",
    )
