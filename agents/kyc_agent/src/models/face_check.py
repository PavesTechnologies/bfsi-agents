import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.utils.migration_database import Base

class FaceCheck(Base):
    __tablename__ = "face_checks"

    id = mapped_column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))

    kyc_attempt_id = mapped_column(
        UUID,
        ForeignKey("kyc_attempts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    face_match_score = mapped_column(Float)
    liveness_passed = mapped_column(Boolean)
    spoof_detected = mapped_column(Boolean)
    face_threshold = mapped_column(Float)

    flags = mapped_column(JSONB)

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )

    kyc_attempt = relationship("KYCAttempt", back_populates="face_check")
