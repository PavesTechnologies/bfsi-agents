from dataclasses import dataclass
from typing import TypedDict, Optional, Dict, List,Annotated
from uuid import UUID
from datetime import datetime


def list_append_reducer(existing, new):
    existing = existing or []
    new = new or []
    return existing + new


def dict_merge_reducer(existing: Dict[str, float] | None,
                        new: Dict[str, float] | None) -> Dict[str, float]:
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
    issued_year: Optional[int]
    flags: Dict[str, str]
    

class AddressVerificationState(TypedDict, total=False):
    address_match: bool
    risk_score: float
    geo_risk_flag: bool
    high_risk_country_flag: bool
    address_type: str
    usps_validated: bool
    deliverable: bool
    standardized_address: Dict[str, str]
    flags: Dict[str, str]

class DocumentCheckState(TypedDict, total=False):
    document_type: str
    issuer_valid: bool
    expiry_valid: bool
    tamper_detected: bool
    format_valid: bool
    document_score: float
    document_expiry_date: Optional[datetime]
    issuing_country: str
    issuing_state: str
    flags: Dict[str, str]
    
class FaceCheckState(TypedDict, total=False):
    face_match_score: float
    liveness_passed: bool
    liveness_score: float
    spoof_detected: bool
    face_threshold: float
    face_detection_confidence: float
    deepfake_score: float
    replay_attack_detected: bool
    flags: Dict[str, str]
    
class AMLCheckState(TypedDict, total=False):
    ofac_match: bool
    ofac_confidence: float
    pep_match: bool
    sanctions_list_version: str
    aml_score: float
    flags: Dict[str, str]
    
    
class RiskDecisionState(TypedDict, total=False):
    final_status: str  # PASS / FAIL / NEEDS_HUMAN_REVIEW
    aggregated_score: float
    hard_fail_triggered: bool
    decision_reason: str
    decision_rules_snapshot: Dict[str, str]
    model_versions: Dict[str, str]
    
# @dataclass(frozen=True)
class Address:
    line1: str
    line2: str
    city: str
    state: str
    zip: str


# @dataclass(frozen=True)
class RawKYCRequest:
    applicant_id: str
    full_name: str
    dob: str
    ssn: str
    address: Address
    phone: str
    email: str
    selfie_image: Optional[str] = None  # Base64 string
    id_card_image: Optional[str] = None  # Base64 string

class KYCState(TypedDict, total=False):

    # Core
    raw_request: RawKYCRequest
   
    # Submodules
    ssn_validation: Optional[SSNValidationState]
    address_verification: Optional[AddressVerificationState]
    document_check: Optional[DocumentCheckState]
    face_check: Optional[FaceCheckState]
    aml_check: Optional[AMLCheckState]

    # Aggregation
    risk_decision: Optional[RiskDecisionState]

    # System
    hard_stop: bool
    parallel_tasks_completed: Annotated[List[str], list_append_reducer]
    node_execution_times: Annotated[Dict[str, float], dict_merge_reducer]