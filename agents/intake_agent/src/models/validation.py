from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from .base import Base


class IntakeValidationResult(Base):
    __tablename__ = "intake_validation_result"

    id = Column(UUID, primary_key=True)
    application_id = Column(UUID, nullable=False)
    field_name = Column(String, nullable=False)
    reason_code = Column(String, nullable=False)
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
