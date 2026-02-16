# src/models/kyc_attempt.py

import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, DateTime, Enum, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from src.utils.migration_database import Base
from .enums import KYCStatus


class KYCAttempt(Base):
    __tablename__ = "kyc_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        nullable=False,
        index=True
    )

    attempt_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[KYCStatus] = mapped_column(
        Enum(KYCStatus, name="kyc_status_enum"),
        nullable=False,
        default=KYCStatus.PENDING,
    )

    confidence_score: Mapped[float | None] = mapped_column(Float)

    rules_version: Mapped[str | None] = mapped_column(String(50))

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    payload_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )

    shadow_decision_status: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # 🔗 Relationships
    identity_check = relationship("IdentityCheck", back_populates="kyc_attempt", uselist=False)
    document_check = relationship("DocumentCheck", back_populates="kyc_attempt", uselist=False)
    face_check = relationship("FaceCheck", back_populates="kyc_attempt", uselist=False)
    aml_check = relationship("AMLCheck", back_populates="kyc_attempt", uselist=False)
    risk_decision = relationship("RiskDecision", back_populates="kyc_attempt", uselist=False)

    vendor_responses = relationship("VendorResponse", back_populates="kyc_attempt")
    evidence_artifacts = relationship("EvidenceArtifact", back_populates="kyc_attempt")
    human_reviews = relationship("HumanReview", back_populates="kyc_attempt")
