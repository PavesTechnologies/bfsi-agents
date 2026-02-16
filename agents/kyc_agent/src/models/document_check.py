from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, DateTime, ForeignKey, text, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.utils.migration_database import Base

class DocumentCheck(Base):
    __tablename__ = "document_checks"

    id = mapped_column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))

    kyc_attempt_id = mapped_column(
        UUID,
        ForeignKey("kyc_attempts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    document_type = mapped_column(String(100))
    issuer_valid = mapped_column(Boolean)
    expiry_valid = mapped_column(Boolean)
    tamper_detected = mapped_column(Boolean)
    format_valid = mapped_column(Boolean)
    document_score = mapped_column(Float)

    flags = mapped_column(JSONB)

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )

    kyc_attempt = relationship("KYCAttempt", back_populates="document_check")
