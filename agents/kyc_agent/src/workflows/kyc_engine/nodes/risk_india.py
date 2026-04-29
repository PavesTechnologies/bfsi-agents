"""
India Risk Aggregation Node.

Evaluates all Indian KYC check results and produces a final
PASS / FAIL / NEEDS_HUMAN_REVIEW decision with a confidence score.

Hard-fail rules (any one → FAIL):
  AADHAAR_NOT_VERIFIED, PAN_NOT_VERIFIED, PAN_AADHAAR_NOT_LINKED,
  VIDEO_KYC_FAILED, FACE_DUPLICATE_FOUND, RBI_SANCTIONS_HIT, UNSC_HIT,
  AGE_BELOW_MINIMUM

Soft-flag rules (2 or more → NEEDS_HUMAN_REVIEW):
  PEP_MATCH, VOIP_PHONE, HIGH_RISK_PHONE, PINCODE_UNKNOWN, CKYC_PENDING
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.utils.audit_decorator import audit_node
from src.workflows.kyc_engine.india_kyc_state import IndiaRiskDecisionState, IndianKYCState

_HARD_FAIL_CHECKS: dict = {
    "AADHAAR_NOT_VERIFIED": lambda s: not (s.get("aadhaar_verification") or {}).get("aadhaar_verified", True),
    "PAN_NOT_VERIFIED": lambda s: not (s.get("pan_verification") or {}).get("pan_verified", True),
    "PAN_AADHAAR_NOT_LINKED": lambda s: not (s.get("pan_verification") or {}).get("pan_aadhaar_linked", True),
    "VIDEO_KYC_FAILED": lambda s: (s.get("video_kyc") or {}).get("status") == "FAILED",
    "FACE_DUPLICATE_FOUND": lambda s: (s.get("face_dedup") or {}).get("is_duplicate", False),
    "RBI_SANCTIONS_HIT": lambda s: (s.get("aml_india") or {}).get("rbi_match", False),
    "UNSC_HIT": lambda s: (s.get("aml_india") or {}).get("unsc_match", False),
    "AGE_BELOW_MINIMUM": lambda s: "AGE_BELOW_MINIMUM" in ((s.get("aadhaar_verification") or {}).get("flags", {})),
}

_SOFT_FLAG_CHECKS: dict = {
    "PEP_MATCH": lambda s: (s.get("aml_india") or {}).get("pep_match", False),
    "VOIP_PHONE": lambda s: (s.get("contact_india") or {}).get("is_voip", False),
    "HIGH_RISK_PHONE": lambda s: (s.get("contact_india") or {}).get("is_high_risk", False),
    "PINCODE_UNKNOWN": lambda s: "PINCODE_UNKNOWN" in ((s.get("address_india") or {}).get("flags", {})),
    "CKYC_PENDING": lambda s: (s.get("ckyc") or {}).get("upload_status") == "PENDING",
}


@track_node("risk_india")
@audit_node(agent_name="kyc_agent")
def risk_india_node(state: IndianKYCState) -> IndianKYCState:
    triggered_hard = [name for name, check in _HARD_FAIL_CHECKS.items() if check(state)]
    triggered_soft = [name for name, check in _SOFT_FLAG_CHECKS.items() if check(state)]

    hard_fail = len(triggered_hard) > 0
    needs_review = not hard_fail and len(triggered_soft) >= 2

    if hard_fail:
        final_status = "FAIL"
    elif needs_review:
        final_status = "NEEDS_HUMAN_REVIEW"
    else:
        final_status = "PASS"

    aadhaar = state.get("aadhaar_verification") or {}
    video = state.get("video_kyc") or {}
    aml = state.get("aml_india") or {}

    aadhaar_score = 1.0 if aadhaar.get("aadhaar_verified") else 0.0
    video_score = video.get("liveness_score", 0.0) if video.get("status") == "COMPLETED" else 0.0
    aml_score = 1.0 - aml.get("aml_score", 0.0)

    confidence_score = round(aadhaar_score * 0.40 + video_score * 0.35 + aml_score * 0.25, 4)

    if hard_fail:
        decision_reason = f"Hard fail triggered: {triggered_hard[0]}"
    elif needs_review:
        decision_reason = f"Multiple soft flags raised: {', '.join(triggered_soft)}"
    else:
        decision_reason = "All Indian KYC checks passed successfully"

    risk_decision: IndiaRiskDecisionState = {
        "final_status": final_status,
        "confidence_score": confidence_score,
        "hard_fail_triggered": hard_fail,
        "decision_reason": decision_reason,
        "triggered_rules": triggered_hard + triggered_soft,
        "soft_flags": triggered_soft,
        "hard_fail_rules": triggered_hard,
        "rule_version": "INDIA-KYC-RULES-2026-Q1",
        "reasoning_trace": {
            "aadhaar_verified": aadhaar.get("aadhaar_verified"),
            "pan_status": (state.get("pan_verification") or {}).get("pan_status"),
            "pan_aadhaar_linked": (state.get("pan_verification") or {}).get("pan_aadhaar_linked"),
            "video_kyc_status": video.get("status"),
            "liveness_score": video.get("liveness_score"),
            "face_duplicate": (state.get("face_dedup") or {}).get("is_duplicate"),
            "aml_score": aml.get("aml_score"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    }

    return {"risk_decision": risk_decision}
