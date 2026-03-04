"""Canonical metadata model and persistence record.

This module defines the Pydantic `RequestMetadata` used across the
service boundary and the `RequestMetadataRecord` SQLAlchemy model used
for persistence.
"""

from pydantic import BaseModel
from typing import Optional
import datetime
import uuid
from sqlalchemy import String, DateTime, Integer, JSON, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.models import Base


class RequestMetadata(BaseModel):
    """Canonical metadata pydantic model (flattened).

    Fields:
    - ip_address (required)
    - user_agent
    - browser
    - os
    - device_type
    - accept_language
    - referrer
    """

    ip_address: str
    user_agent: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    device_type: Optional[str] = None
    accept_language: Optional[str] = None
    referrer: Optional[str] = None


class RequestMetadataRecord(Base):
    """SQLAlchemy persistence model for request metadata."""

    __tablename__ = "request_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        unique=True,
        index=True,
    )
    app_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        index=True,
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    browser: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    device_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    accept_language: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    referrer: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"RequestMetadataRecord(request_id={self.request_id}, ip={self.ip_address}, "
            f"device={self.device_type}, browser={self.browser}, os={self.os})"
        )
