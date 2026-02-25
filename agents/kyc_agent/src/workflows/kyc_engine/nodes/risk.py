"""
Risk Aggregator Node – Deterministic Decision Engine
"""

import time
from typing import Dict, List
from src.workflows.kyc_engine.kyc_state import KYCState
from src.core.telemetry import track_node

# ---- Threshold Config (Versioned) ----
FACE_MATCH_THRESHOLD = 0.75
LIVENESS_THRESHOLD = 0.80

@track_node("risk_aggregator")
def risk_aggregator_node(state: KYCState) -> KYCState:
    start = time.time()

    ssn = state.get("ssn_validation") or {}
    address = state.get("address_verification") or {}
    document = state.get("document_check") or {}
    face = state.get("face_check") or {}
    aml = state.get("aml_check") or {}

    triggered_rules: List[str] = []
    hard_fail = False
    final_status = "PASS"
    reason = "All checks passed"

    # ==================================================
    # LAYER 1 — HARD FAIL (NON-NEGOTIABLE)
    # ==================================================

    if aml.get("ofac_match"):
        triggered_rules.append("OFAC_MATCH")
        hard_fail = True

    if ssn.get("deceased_flag"):
        triggered_rules.append("SSN_DECEASED")

    if ssn.get("identity_theft_flag"):
        triggered_rules.append("IDENTITY_THEFT_FLAG")

    if document.get("tamper_detected"):
        triggered_rules.append("DOCUMENT_TAMPER")

    if face.get("spoof_detected") or face.get("replay_attack_detected"):
        triggered_rules.append("BIOMETRIC_SPOOF")

    if triggered_rules:
        final_status = "FAIL"
        reason = "Hard fail condition triggered"
        hard_fail = True

    # ==================================================
    # LAYER 2 — HUMAN REVIEW CONDITIONS
    # ==================================================

    if not hard_fail:

        review_rules = []

        if face.get("face_match_score", 1.0) < FACE_MATCH_THRESHOLD:
            review_rules.append("LOW_FACE_MATCH")

        if face.get("liveness_score", 1.0) < LIVENESS_THRESHOLD:
            review_rules.append("LOW_LIVENESS_SCORE")

        if not document.get("expiry_valid", True):
            review_rules.append("DOCUMENT_EXPIRED")

        if aml.get("pep_match"):
            review_rules.append("PEP_MATCH")

        if address.get("geo_risk_flag"):
            review_rules.append("HIGH_GEO_RISK")

        if review_rules:
            final_status = "NEEDS_HUMAN_REVIEW"
            reason = "Soft risk condition(s) triggered"
            triggered_rules.extend(review_rules)

    # ==================================================
    # LAYER 3 — SCORE AGGREGATION (OPTIONAL)
    # ==================================================

    aggregated_score = (
        ssn.get("ssn_score", 1.0) * 0.3 +
        document.get("document_score", 1.0) * 0.2 +
        face.get("face_match_score", 1.0) * 0.3 +
        (1 - aml.get("aml_score", 0.0)) * 0.2
    )

    # ==================================================
    # DECISION SNAPSHOT (AUDIT SAFE)
    # ==================================================

    decision_snapshot: Dict[str, bool] = {
        "ofac_match": aml.get("ofac_match", False),
        "face_match_below_threshold": face.get("face_match_score", 1.0) < FACE_MATCH_THRESHOLD,
        "document_tamper": document.get("tamper_detected", False),
        "identity_theft_flag": ssn.get("identity_theft_flag", False),
        "pep_match": aml.get("pep_match", False),
    }

    duration = time.time() - start

    return {
        "risk_decision": {
            "final_status": final_status,
            "aggregated_score": round(aggregated_score, 3),
            "hard_fail_triggered": hard_fail,
            "decision_reason": reason,
            "decision_rules_snapshot": decision_snapshot,
            "triggered_rules": triggered_rules,
            "model_versions": {
                "face_threshold": str(FACE_MATCH_THRESHOLD),
                "liveness_threshold": str(LIVENESS_THRESHOLD),
                "aggregator_version": "v1.0"
            }
        },
        "node_execution_times": {"aggregate": duration}
    }