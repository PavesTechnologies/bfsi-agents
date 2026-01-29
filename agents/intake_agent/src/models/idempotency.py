from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()


class IntakeIdempotency(Base):
    __tablename__ = "intake_idempotency"

    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID(as_uuid=True), nullable=False)

    request_hash = Column(String(64), nullable=False)

    status = Column(String(32), nullable=False)

    response_payload = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
