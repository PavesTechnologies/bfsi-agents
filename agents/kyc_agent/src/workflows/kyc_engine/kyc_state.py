"""
KYC State Definition

Defines the shared state model for the KYC compliance pipeline.
State flows deterministically through: Identity → AML → Risk → Decision
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


# =========================
# Enums
# =========================

class EventType(str, Enum):
    """Types of events in the KYC pipeline."""
    IDENTITY_STARTED = "identity_started"
    IDENTITY_COMPLETE = "identity_complete"
    IDENTITY_FAILED = "identity_failed"

    AML_STARTED = "aml_started"
    AML_COMPLETE = "aml_complete"
    AML_FAILED = "aml_failed"

    RISK_STARTED = "risk_started"
    RISK_COMPLETE = "risk_complete"
    RISK_FAILED = "risk_failed"

    DECISION_MADE = "decision_made"
    PIPELINE_FAILED = "pipeline_failed"


class KYCStatus(str, Enum):
    """Regulatory KYC decision status."""
    PENDING = "PENDING"
    PASSED = "PASSED"
    REVIEW = "REVIEW"
    FAILED = "FAILED"


class KYCDecision(str, Enum):
    """Final KYC decision outcome."""
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# =========================
# Audit History
# =========================

class HistoryEntry(BaseModel):
    """Single entry in the execution history."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event: EventType
    node: str = Field(..., description="Node that emitted event")
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


# =========================
# Node Results
# =========================

class IdentityResult(BaseModel):
    """Result of identity verification node."""
    verified: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    matched_documents: List[str] = Field(default_factory=list)
    anomalies: List[str] = Field(default_factory=list)


class AMLResult(BaseModel):
    """Result of AML screening node."""
    matches_found: int = 0
    match_details: List[Dict[str, Any]] = Field(default_factory=list)
    sources_checked: List[str] = Field(default_factory=list)

    # Compliance critical signals
    ofac_match: bool = False
    pep_match: bool = False


class RiskAssessment(BaseModel):
    """Result of risk assessment node."""
    risk_level: RiskLevel = Field(..., description="LOW, MEDIUM, or HIGH")
    risk_score: float = Field(ge=0.0, le=1.0)
    decision_factors: List[str] = Field(default_factory=list)


class FinalDecision(BaseModel):
    """Final KYC decision."""
    decision: KYCDecision = Field(..., description="PASS, REVIEW, or FAIL")
    rationale: str


# =========================
# Main State
# =========================

class KYCState(BaseModel):
    """
    Shared state passed through the KYC compliance pipeline.

    Deterministic flow:
    1. Identity Verification
    2. AML Screening
    3. Risk Assessment
    4. Final Decision

    All state changes are recorded for audit replay.
    """

    # Identifiers
    application_id: str = Field(..., description="Unique application identifier")
    execution_id: str = Field(..., description="Unique execution ID for replay and audit")

    # Replay & Idempotency Metadata
    attempt_version: int = Field(
        default=1,
        description="Incremented each time KYC is re-run for the same application"
    )

    idempotency_key: Optional[str] = Field(
        default=None,
        description="Unique key from orchestrator used to prevent duplicate execution"
    )

    input_payload_hash: Optional[str] = Field(
        default=None,
        description="SHA-256 hash of normalized applicant input used for replay verification"
    )

    # Applicant Data
    applicant_data: Dict[str, Any] = Field(default_factory=dict)

    # Node Results
    identity: Optional[IdentityResult] = None
    aml: Optional[AMLResult] = None
    risk: Optional[RiskAssessment] = None
    decision: Optional[FinalDecision] = None

    # Pipeline Status
    status: KYCStatus = Field(default=KYCStatus.PENDING)
    current_stage: Optional[str] = None
    error: Optional[str] = None
    hard_fail_triggered: bool = False

    # Regulatory Flags (Explainability)
    flags: List[str] = Field(default_factory=list)

    # Compliance Metrics
    confidence_score: Optional[float] = None

    # Audit Trail
    history: List[HistoryEntry] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True

    # =========================
    # Helpers
    # =========================

    def add_history_entry(
        self,
        event: EventType,
        node: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Append event to audit history."""
        entry = HistoryEntry(
            event=event,
            node=node,
            data=data or {},
            error=error,
        )
        self.history.append(entry)
        self.updated_at = datetime.utcnow()
