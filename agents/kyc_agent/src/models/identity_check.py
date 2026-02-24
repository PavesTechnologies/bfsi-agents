# src/models/identity_check.py
import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.utils.migration_database import Base


class IdentityCheck(Base):
    __tablename__ = "identity_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # relations
    kyc_id = Column(UUID(as_uuid=True), ForeignKey("kyc_cases.id"), nullable=False)
    applicant_id = Column(String, nullable=False)

    # 🔹 decision summary (indexed/query-heavy fields)
    final_status = Column(String, nullable=False)
    aggregated_score = Column(Float, nullable=True)
    hard_fail_triggered = Column(Boolean, nullable=True)

    # 🔹 important SSN flags (frequently filtered)
    ssn_valid = Column(Boolean, nullable=True)
    ssn_plausible = Column(Boolean, nullable=True)
    name_ssn_match = Column(Boolean, nullable=True)
    dob_ssn_match = Column(Boolean, nullable=True)
    deceased_flag = Column(Boolean, nullable=True)

    # 🔹 flexible payloads (audit / model metadata)
    ssn_risk_snapshot = Column(JSON, nullable=True)
    decision_rules_snapshot = Column(JSON, nullable=True)
    model_versions = Column(JSON, nullable=True)
    audit_payload = Column(JSON, nullable=True)

    # 🔹 metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
