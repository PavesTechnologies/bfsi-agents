# src/models/document_check.py
import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, DateTime, ForeignKey, text, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.utils.migration_database import Base
from .kyc_cases import KYC

class DocumentCheck(Base):
    __tablename__ = "document_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    kyc_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("kyc_cases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # 1:1
        index=True,
    )

    document_type: Mapped[str | None] = mapped_column(String(100))

    issuer_valid: Mapped[bool | None] = mapped_column(Boolean)
    expiry_valid: Mapped[bool | None] = mapped_column(Boolean)
    tamper_detected: Mapped[bool | None] = mapped_column(Boolean)
    format_valid: Mapped[bool | None] = mapped_column(Boolean)

    document_score: Mapped[float | None] = mapped_column(Float)

    flags: Mapped[dict | None] = mapped_column(JSONB)

    document_expiry_date: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    
    issuing_country: Mapped[str | None] = mapped_column(String(50))
    issuing_state: Mapped[str | None] = mapped_column(String(50))
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # 🔗 Relationship back to parent
    kyc: Mapped["KYC"] = relationship(
        "KYC",
        back_populates="document_check"
    )
