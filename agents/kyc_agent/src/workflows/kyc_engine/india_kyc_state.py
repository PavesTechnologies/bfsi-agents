from typing import Annotated, TypedDict


def list_append_reducer(existing, new):
    existing = existing or []
    new = new or []
    return existing + new


def dict_merge_reducer(existing, new):
    existing = existing or {}
    new = new or {}
    return {**existing, **new}


class AadhaarVerificationState(TypedDict, total=False):
    aadhaar_verified: bool
    name_match: bool
    dob_match: bool
    masked_aadhaar: str
    address_from_aadhaar: dict[str, str]
    photo_base64: str
    otp_status: str    # OTP_SENT | OTP_VERIFIED | OTP_EXPIRED | NOT_FOUND
    flags: dict[str, str]


class PANVerificationState(TypedDict, total=False):
    pan_verified: bool
    name_match: bool
    pan_status: str    # ACTIVE | INACTIVE | FLAGGED | INVALID_FORMAT
    pan_aadhaar_linked: bool
    flags: dict[str, str]


class VideoKYCState(TypedDict, total=False):
    session_id: str
    status: str        # COMPLETED | FAILED | PENDING
    liveness_score: float
    face_match_score: float
    geo_within_india: bool
    geo_location: dict[str, float]
    consent_recorded: bool
    ovd_captured: bool
    failure_reason: str | None
    flags: dict[str, str]


class FaceDeduplicationState(TypedDict, total=False):
    is_duplicate: bool
    matching_applicant_ids: list[str]
    highest_similarity: float
    flags: dict[str, str]


class AMLIndiaState(TypedDict, total=False):
    rbi_match: bool
    unsc_match: bool
    pep_match: bool
    aml_score: float
    watchlist_version: str
    flags: dict[str, str]


class ContactIndiaState(TypedDict, total=False):
    phone_valid: bool
    is_voip: bool
    is_high_risk: bool
    formatted_phone: str
    flags: dict[str, str]


class AddressIndiaState(TypedDict, total=False):
    address_valid: bool
    pincode_valid: bool
    state: str
    district: str
    standardized_address: dict[str, str]
    flags: dict[str, str]


class CKYCState(TypedDict, total=False):
    ckyc_id: str | None
    upload_status: str    # SUCCESS | PENDING | FAILED
    uploaded_at: str | None
    flags: dict[str, str]


class IndiaRiskDecisionState(TypedDict, total=False):
    final_status: str      # PASS | FAIL | NEEDS_HUMAN_REVIEW
    confidence_score: float
    hard_fail_triggered: bool
    decision_reason: str
    triggered_rules: list[str]
    soft_flags: list[str]
    hard_fail_rules: list[str]
    rule_version: str
    reasoning_trace: dict | None


class RawIndianKYCRequest(TypedDict, total=False):
    applicant_id: str
    full_name: str
    dob: str               # YYYY-MM-DD
    aadhaar_number: str    # 12 digits, spaces stripped
    aadhaar_otp: str | None
    pan_number: str        # [A-Z]{5}[0-9]{4}[A-Z]
    address: dict[str, str]   # line1, line2, city, state, pincode
    phone: str
    email: str


class IndianKYCState(TypedDict, total=False):
    # Core
    raw_request: RawIndianKYCRequest

    # Substates
    aadhaar_verification: AadhaarVerificationState | None
    pan_verification: PANVerificationState | None
    video_kyc: VideoKYCState | None
    face_dedup: FaceDeduplicationState | None
    aml_india: AMLIndiaState | None
    contact_india: ContactIndiaState | None
    address_india: AddressIndiaState | None
    ckyc: CKYCState | None

    # Aggregation
    risk_decision: IndiaRiskDecisionState | None

    # Explanation
    decision_explanation: str

    # System
    hard_stop: bool
    parallel_tasks_completed: Annotated[list[str], list_append_reducer]
    node_execution_times: Annotated[dict[str, float], dict_merge_reducer]
