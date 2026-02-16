# src/models/evidence_artifact.py

import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, DateTime, ForeignKey, text, String, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.utils.migration_database import Base
from .enums import ArtifactType
from .kyc_cases import KYC

class EvidenceArtifact(Base):
    __tablename__ = "evidence_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    kyc_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("kyc_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType, name="artifact_type_enum"),
        nullable=False,
        index=True,
    )

    mime_type = mapped_column(String(100))
    
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    file_hash: Mapped[str | None] = mapped_column(String(255))
    
    additional_metadata: Mapped[dict] = mapped_column(JSONB)
    
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # 🔗 Relationship
    kyc: Mapped["KYC"] = relationship(
        "KYC",
        back_populates="evidence_artifacts",
    )
