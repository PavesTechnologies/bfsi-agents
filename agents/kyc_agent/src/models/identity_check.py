# src/models/identity_check.py
import uuid

from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from src.utils.migration_database import Base


class IdentityCheck(Base):
    __tablename__ = "identity_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kyc_id = Column(UUID(as_uuid=True), ForeignKey("kyc_cases.id"), nullable=False)
    applicant_id = Column(String, nullable=False)
    final_status = Column(String, nullable=False)
    risk_payload = Column(JSON, nullable=True)
