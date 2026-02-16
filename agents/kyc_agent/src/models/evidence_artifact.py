from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, DateTime, ForeignKey, text, String, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.utils.migration_database import Base
from .enums import ArtifactType


class EvidenceArtifact(Base):
    __tablename__ = "evidence_artifacts"

    id = mapped_column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))

    kyc_attempt_id = mapped_column(
        UUID,
        ForeignKey("kyc_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )

    artifact_type = mapped_column(
        Enum(ArtifactType, name="artifact_type_enum"),
        nullable=False,
    )

    storage_path = mapped_column(String(500))
    file_hash = mapped_column(String(255))
    encrypted = mapped_column(Boolean)

    created_at = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    kyc_attempt = relationship("KYCAttempt", back_populates="evidence_artifacts")
