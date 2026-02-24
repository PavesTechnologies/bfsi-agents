# src/models/aml_check.py

import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.migration_database import Base

from .kyc_cases import KYC


class AMLCheck(Base):
    __tablename__ = "aml_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    kyc_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("kyc_cases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 1:1 relationship
        index=True,
    )

    ofac_match: Mapped[bool | None] = mapped_column(Boolean, index=True)

    ofac_confidence: Mapped[float | None] = mapped_column(Float)

    pep_match: Mapped[bool | None] = mapped_column(Boolean)

    sanctions_list_version: Mapped[str | None] = mapped_column(String(100))

    aml_score: Mapped[float | None] = mapped_column(Float)

    flags: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # 🔗 Relationship back to parent
    kyc: Mapped["KYC"] = relationship("KYC", back_populates="aml_check")
