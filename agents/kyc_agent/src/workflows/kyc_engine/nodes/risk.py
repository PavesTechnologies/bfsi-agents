"""
Risk Aggregator Node
"""

import time
from src.workflows.kyc_engine.kyc_state import KYCState


def risk_aggregator_node(state: KYCState) -> KYCState:
    start = time.time()

    ssn = state.get("ssn_validation", {})
    doc = state.get("document_check", {})
    face = state.get("face_check", {})
    aml = state.get("aml_check", {})

    final_status = "PASS"
    hard_fail = False
    reason = "All checks passed"

    # Hard stop: OFAC
    if aml.get("ofac_match"):
        final_status = "FAIL"
        hard_fail = True
        reason = "OFAC match detected"

    # Soft fail: low face match
    elif face.get("face_match_score", 1) < 0.75:
        final_status = "NEEDS_HUMAN_REVIEW"
        reason = "Low face match confidence"

    ssn_summary = {
        "ssn_valid": ssn.get("ssn_valid"),
        "ssn_plausible": ssn.get("ssn_plausible"),
        "name_ssn_match": ssn.get("name_ssn_match"),
        "dob_ssn_match": ssn.get("dob_ssn_match"),
        "deceased_flag": ssn.get("deceased_flag"),
        "issued_year": ssn.get("issued_year"),
        "ssn_flags": ssn.get("flags", {})
    }

    result = {
        "final_status": final_status,
        "aggregated_score": 0.95,
        "hard_fail_triggered": hard_fail,
        "decision_reason": reason,
        "ssn_risk_snapshot": ssn_summary,
        "decision_rules_snapshot": {},
        "model_versions": {}
    }

    duration = time.time() - start

    return {
        "risk_decision": result,
        "node_execution_times": {"aggregate": duration}
    }