from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, DateTime, ForeignKey, text, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from src.utils.migration_database import Base


class VendorResponse(Base):
    __tablename__ = "vendor_responses"

    id = mapped_column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))

    kyc_attempt_id = mapped_column(
        UUID,
        ForeignKey("kyc_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )

    vendor_name = mapped_column(String(100))
    vendor_service = mapped_column(String(100))
    response_hash = mapped_column(String(255))
    raw_response_location = mapped_column(String(500))
    success = mapped_column(Boolean)
    response_time_ms = mapped_column(Integer)

    created_at = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    kyc_attempt = relationship("KYCAttempt", back_populates="vendor_responses")
