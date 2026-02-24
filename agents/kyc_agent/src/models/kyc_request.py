# src/models/kyc_request.py

import datetime
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.migration_database import Base

from .enums import IdempotencyStatus
from .kyc_cases import KYC


class KYCRequest(Base):
    __tablename__ = "kyc_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    payload_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    kyc_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("kyc_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    response_payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    response_status: Mapped[IdempotencyStatus] = mapped_column(
        Enum(IdempotencyStatus, name="idempotency_status_enum"),
        nullable=False,
        default=IdempotencyStatus.PENDING,
    )

    responded_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # 🔗 Relationship
    kyc: Mapped["KYC"] = relationship(
        "KYC",
        back_populates="requests",
    )
