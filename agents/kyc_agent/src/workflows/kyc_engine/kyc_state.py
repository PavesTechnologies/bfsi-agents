from datetime import datetime
from typing import Annotated, TypedDict


def list_append_reducer(existing, new):
    existing = existing or []
    new = new or []
    return existing + new


def dict_merge_reducer(
    existing: dict[str, float] | None, new: dict[str, float] | None
) -> dict[str, float]:
    existing = existing or {}
    new = new or {}
    return {**existing, **new}


class SSNValidationState(TypedDict, total=False):
    ssn_valid: bool
    ssn_plausible: bool
    identity_theft_flag: bool
    deceased_flag: bool
    ssn_score: float
    name_ssn_match: bool
    dob_ssn_match: bool
    issued_year: int | None
    flags: dict[str, str]


class AddressVerificationState(TypedDict, total=False):
    address_match: bool
    risk_score: float
    geo_risk_flag: bool
    high_risk_country_flag: bool
    address_type: str
    usps_validated: bool
    deliverable: bool
    standardized_address: dict[str, str]
    flags: dict[str, str]


class DocumentCheckState(TypedDict, total=False):
    document_type: str
    issuer_valid: bool
    expiry_valid: bool
    tamper_detected: bool
    format_valid: bool
    document_score: float
    document_expiry_date: datetime | None
    issuing_country: str
    issuing_state: str
    flags: dict[str, str]


class FaceCheckState(TypedDict, total=False):
    face_match_score: float
    liveness_passed: bool
    liveness_score: float
    spoof_detected: bool
    face_threshold: float
    face_detection_confidence: float
    deepfake_score: float
    replay_attack_detected: bool
    flags: dict[str, str]


class AMLCheckState(TypedDict, total=False):
    ofac_match: bool
    ofac_confidence: float
    pep_match: bool
    sanctions_list_version: str
    aml_score: float
    flags: dict[str, str]


class RiskDecisionState(TypedDict, total=False):
    """
    Final deterministic KYC decision output.
    Fully aligned with rule-engine + audit requirements.
    """

    # -------------------------------------------------
    # Core Decision
    # -------------------------------------------------
    final_status: str  # PASS | FAIL | NEEDS_HUMAN_REVIEW
    confidence_score: float  # 0.0 – 1.0 normalized trust score
    hard_fail_triggered: bool
    decision_reason: str

    # -------------------------------------------------
    # Rule Execution Details
    # -------------------------------------------------
    triggered_rules: list[str]  # All rules that fired
    soft_flags: list[str]  # Soft rules triggered
    hard_fail_rules: list[str]  # Hard rules triggered (if any)

    # -------------------------------------------------
    # Policy Versioning
    # -------------------------------------------------
    rule_version: str  # YAML version (e.g. 2026.02.25.v1)
    rule_file_hash: str | None  # SHA256 of rule file (immutability)

    # -------------------------------------------------
    # Decision Snapshot (Audit Safe)
    # -------------------------------------------------
    decision_rules_snapshot: dict[str, bool]
    input_payload_hash: str | None
    vendor_signal_hash: str | None

    # -------------------------------------------------
    # Model & Threshold Versions
    # -------------------------------------------------
    model_versions: dict[str, str]  # threshold versions, aggregator version

    # -------------------------------------------------
    # Explainability / Compliance
    # -------------------------------------------------
    reasoning_trace: dict | None  # Full replay object (encrypted at rest)


# @dataclass(frozen=True)
class Address:
    line1: str
    line2: str
    city: str
    state: str
    zip: str


class ContactVerificationState(TypedDict):
    phone_valid: bool
    email_valid: bool
    is_high_risk_phone: bool
    is_disposable_email: bool
    formatted_phone: str
    flags: dict[str, str]


# @dataclass(frozen=True)
class RawKYCRequest:
    applicant_id: str
    full_name: str
    dob: str
    ssn: str
    address: Address
    phone: str
    email: str


class KYCState(TypedDict, total=False):
    # Core
    raw_request: RawKYCRequest

    # Submodules
    ssn_validation: SSNValidationState | None
    address_verification: AddressVerificationState | None
    contact_verification: ContactVerificationState | None
    document_check: DocumentCheckState | None
    face_check: FaceCheckState | None
    aml_check: AMLCheckState | None

    # Aggregation
    risk_decision: RiskDecisionState | None

    # explaination
    decision_explanation: str

    # System
    hard_stop: bool
    parallel_tasks_completed: Annotated[list[str], list_append_reducer]
    node_execution_times: Annotated[dict[str, float], dict_merge_reducer]
