# src/models/face_check.py

import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.migration_database import Base

from .kyc_cases import KYC


class FaceCheck(Base):
    __tablename__ = "face_checks"

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

    face_match_score: Mapped[float | None] = mapped_column(Float)

    liveness_passed: Mapped[bool | None] = mapped_column(Boolean)

    liveness_score: Mapped[float | None] = mapped_column(Float)

    spoof_detected: Mapped[bool | None] = mapped_column(Boolean)

    face_threshold: Mapped[float | None] = mapped_column(Float)

    face_detection_confidence: Mapped[float | None] = mapped_column(Float)

    deepfake_score: Mapped[float | None] = mapped_column(Float)

    replay_attack_detected: Mapped[bool | None] = mapped_column(Boolean)

    flags: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # 🔗 Relationship back to parent
    kyc: Mapped["KYC"] = relationship("KYC", back_populates="face_check")
