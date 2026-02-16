import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, DateTime, ForeignKey, text, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.utils.migration_database import Base

class AMLCheck(Base):
    __tablename__ = "aml_checks"

    id = mapped_column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))

    kyc_attempt_id = mapped_column(
        UUID,
        ForeignKey("kyc_attempts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    ofac_match = mapped_column(Boolean, index=True)
    ofac_confidence = mapped_column(Float)
    pep_match = mapped_column(Boolean)
    sanctions_list_version = mapped_column(String(100))
    aml_score = mapped_column(Float)

    flags = mapped_column(JSONB)

    created_at = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    kyc_attempt = relationship("KYCAttempt", back_populates="aml_check")
