# src/models/vendor_response.py

import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Integer, DateTime, ForeignKey, text, String
from sqlalchemy.dialects.postgresql import UUID
from src.utils.migration_database import Base
from .kyc_cases import KYC

class VendorResponse(Base):
    __tablename__ = "vendor_responses"

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

    vendor_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    vendor_service: Mapped[str | None] = mapped_column(String(100))

    response_hash: Mapped[str | None] = mapped_column(String(255))

    raw_response_location: Mapped[str | None] = mapped_column(String(500))

    success: Mapped[bool | None] = mapped_column(Boolean)

    response_time_ms: Mapped[int | None] = mapped_column(Integer)

    http_status_code = mapped_column(Integer)

    error_message: Mapped[str | None] = mapped_column(String(255))
    
    retry_count = mapped_column(Integer, default=0)

    request_payload_hash = mapped_column(String(255))

    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # 🔗 Relationship
    kyc: Mapped["KYC"] = relationship(
        "KYC",
        back_populates="vendor_responses"
    )
