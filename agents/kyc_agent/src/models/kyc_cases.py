# src/models/kyc_attempt.py

import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, DateTime, Enum, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from src.utils.migration_database import Base
from .enums import KYCStatus
from sqlalchemy.dialects.postgresql import JSONB

class KYC(Base):
    __tablename__ = "kyc_cases"

    id = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    applicant_id = mapped_column(
        UUID,
        nullable=False,
        index=True
    )

    payload_hash = mapped_column(
        String(64),
        nullable=False,
        index=True
    )

    status = mapped_column(
        Enum(KYCStatus, name="kyc_status_enum"),
        nullable=False,
        default=KYCStatus.PENDING,
        index=True
    )

    confidence_score = mapped_column(Float)

    # Different KYC providers might have different rules and models, so we snapshot them at the time of the attempt
    # EX: "kyc_v1" 
    rules_version = mapped_column(String(50))
    model_versions = mapped_column(JSONB) # model name -> version
    threshold_snapshot = mapped_column(JSONB) # model name -> threshold used for pass/fail

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
        index=True
    )

    completed_at = mapped_column(DateTime(timezone=True))

    # 🔗 One-to-One relationships
    identity_check = relationship(
        "IdentityCheck",
        back_populates="kyc",
        uselist=False,
        cascade="all, delete-orphan"
    )

    document_check = relationship(
        "DocumentCheck",
        back_populates="kyc",
        uselist=False,
        cascade="all, delete-orphan"
    )

    face_check = relationship(
        "FaceCheck",
        back_populates="kyc",
        uselist=False,
        cascade="all, delete-orphan"
    )

    aml_check = relationship(
        "AMLCheck",
        back_populates="kyc",
        uselist=False,
        cascade="all, delete-orphan"
    )

    risk_decision = relationship(
        "RiskDecision",
        back_populates="kyc",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    evidence_artifacts = relationship(
    "EvidenceArtifact",
    back_populates="kyc",
    cascade="all, delete-orphan",
    )

    vendor_responses = relationship(
    "VendorResponse",
    back_populates="kyc",
    cascade="all, delete-orphan",
    )

    human_reviews = relationship(
    "HumanReview",
    back_populates="kyc",
    cascade="all, delete-orphan",
    )
