import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.migration_database import Base

from .kyc_cases import KYC


class AddressVerification(Base):
    __tablename__ = "address_verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    kyc_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("kyc_cases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    address_match: Mapped[bool | None] = mapped_column(Boolean)

    risk_score: Mapped[float | None] = mapped_column(Float)

    geo_risk_flag: Mapped[bool | None] = mapped_column(Boolean)
    high_risk_country_flag: Mapped[bool | None] = mapped_column(Boolean)

    flags: Mapped[dict | None] = mapped_column(JSONB)

    address_type: Mapped[str | None] = mapped_column(String(50), nullable=False)

    usps_validated: Mapped[bool | None] = mapped_column(Boolean, nullable=False)

    deliverable: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    standardized_address: Mapped[dict | None] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # 🔗 Relationship
    kyc: Mapped["KYC"] = relationship(
        "KYC",
        back_populates="address_verification",
    )
