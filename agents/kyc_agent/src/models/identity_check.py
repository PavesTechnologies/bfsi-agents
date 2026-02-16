# src/models/identity_check.py
from .kyc_cases import KYC
import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.utils.migration_database import Base


class IdentityCheck(Base):
    __tablename__ = "identity_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # 🔥 Updated FK reference
    kyc_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("kyc_cases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 1:1 relationship
        index=True,
    )

    # Identity verification signals
    ssn_valid: Mapped[bool | None] = mapped_column(Boolean)
    ssn_plausible: Mapped[bool | None] = mapped_column(Boolean)
    name_dob_match: Mapped[bool | None] = mapped_column(Boolean)
    address_match: Mapped[bool | None] = mapped_column(Boolean)
    phone_match: Mapped[bool | None] = mapped_column(Boolean)
    email_match: Mapped[bool | None] = mapped_column(Boolean)

    identity_score: Mapped[float | None] = mapped_column(Float)

    # Structured flags for explainability
    flags: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # 🔗 Relationship back to parent
    kyc: Mapped["KYC"] = relationship(
        "KYC",
        back_populates="identity_check",
    )
