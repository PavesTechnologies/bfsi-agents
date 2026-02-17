import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.utils.migration_database import Base
from .kyc_cases import KYC

class SSNValidation(Base):
    __tablename__ = "ssn_validations"

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

    # SSN validation signals
    ssn_valid: Mapped[bool | None] = mapped_column(Boolean)
    ssn_plausible: Mapped[bool | None] = mapped_column(Boolean)

    # Optional fraud flags
    identity_theft_flag: Mapped[bool | None] = mapped_column(Boolean)
    
    deceased_flag: Mapped[bool | None] = mapped_column(Boolean)

    ssn_score: Mapped[float | None] = mapped_column(Float)

    flags: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # ---------------------------------------------------------
    # Identity Matching Signals
    # ---------------------------------------------------------

    name_ssn_match: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="Indicates whether applicant name matches SSN record."
    )

    dob_ssn_match: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="Indicates whether applicant date of birth matches SSN record."
    )

    issued_year: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Approximate year SSN was issued (used for fraud pattern detection)."
    )

    
    # 🔗 Relationship
    kyc: Mapped["KYC"] = relationship(
        "KYC",
        back_populates="ssn_validation",
    )
