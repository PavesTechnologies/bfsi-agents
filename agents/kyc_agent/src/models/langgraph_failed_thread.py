import uuid
import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.utils.migration_database import Base

class KYCFailedThread(Base):
    __tablename__ = "kyc_failed_threads"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    # Business Identifier
    application_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True  # one active failure per application
    )

    # LangGraph Thread ID
    thread_id: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    # Failure Info
    failed_node: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Retry tracking (optional but useful)
    retry_count: Mapped[int] = mapped_column(
        default=0,
        server_default=text("0")
    )

    # Timestamp
    failed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP")
    )