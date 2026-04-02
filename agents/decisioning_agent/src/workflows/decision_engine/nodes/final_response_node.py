"""
Final Response Composer
LOS-Compatible Structured Output Builder
"""

from datetime import datetime

from src.domain.audit.narrative_builder import build_audit_narrative
from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node


@track_node("final_response_engine")
@audit_node(agent_name="decisioning_agent")
def final_response_node(state: LoanApplicationState) -> LoanApplicationState:

    final_decision = state.get("final_decision", {})
    counter_offer = state.get("counter_offer_data")
    human_review_packet = state.get("human_review_packet")
    decision_type = final_decision.get("decision", "UNKNOWN")

    # ==================================================
    # Build the structured response payload
    # ==================================================
    response_payload = {
        "application_id": state.get("application_id"),
        "correlation_id": state.get("correlation_id"),
        "policy_version": (state.get("policy_metadata") or {}).get("policy_version"),
        "decision": decision_type,
        "risk_tier": state.get("aggregated_risk_tier"),
        "risk_score": state.get("aggregated_risk_score"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if decision_type == "APPROVE":
        response_payload["loan_details"] = {
            "approved_amount": final_decision.get("approved_amount"),
            "approved_tenure_months": final_decision.get("approved_tenure"),
            "interest_rate": final_decision.get("interest_rate"),
            "disbursement_amount": final_decision.get("disbursement_amount"),
            "explanation": final_decision.get("explanation"),
        }

    elif decision_type == "COUNTER_OFFER":
        response_payload["counter_offer"] = counter_offer
        response_payload["original_decision_explanation"] = final_decision.get("explanation")

    elif decision_type == "REFER_TO_HUMAN":
        response_payload["review_packet"] = human_review_packet
        response_payload["original_decision_explanation"] = final_decision.get("explanation")
        response_payload["primary_reason_key"] = final_decision.get("primary_reason_key")
        response_payload["secondary_reason_key"] = final_decision.get("secondary_reason_key")
        response_payload["adverse_action_reasons"] = final_decision.get("adverse_action_reasons", [])
        response_payload["reasoning_summary"] = final_decision.get("reasoning_summary")
        response_payload["key_factors"] = final_decision.get("key_factors", [])
        response_payload["candidate_reason_codes"] = final_decision.get("candidate_reason_codes", [])
        response_payload["selected_reason_codes"] = final_decision.get("selected_reason_codes", [])
        response_payload["policy_citations"] = final_decision.get("policy_citations", [])
        response_payload["retrieval_evidence"] = final_decision.get("retrieval_evidence", [])
        response_payload["feature_attribution_summary"] = final_decision.get("feature_attribution_summary")
        response_payload["explanation_generation_mode"] = final_decision.get("explanation_generation_mode")
        response_payload["critic_failures"] = final_decision.get("critic_failures", [])

    elif decision_type == "DECLINE":
        adverse_action_reasons = final_decision.get("adverse_action_reasons", [])
        response_payload["decline_reason"] = (
            adverse_action_reasons[0]["official_text"]
            if adverse_action_reasons
            else final_decision.get("explanation")
        )
        response_payload["primary_reason_key"] = final_decision.get("primary_reason_key")
        response_payload["secondary_reason_key"] = final_decision.get("secondary_reason_key")
        response_payload["adverse_action_reasons"] = adverse_action_reasons
        response_payload["adverse_action_notice"] = final_decision.get("adverse_action_notice")
        response_payload["reasoning_summary"] = final_decision.get("reasoning_summary")
        response_payload["key_factors"] = final_decision.get("key_factors", [])
        response_payload["reasoning_steps"] = final_decision.get("reasoning_steps", [])
        response_payload["candidate_reason_codes"] = final_decision.get("candidate_reason_codes", [])
        response_payload["selected_reason_codes"] = final_decision.get("selected_reason_codes", [])
        response_payload["policy_citations"] = final_decision.get("policy_citations", [])
        response_payload["retrieval_evidence"] = final_decision.get("retrieval_evidence", [])
        response_payload["feature_attribution_summary"] = final_decision.get("feature_attribution_summary")
        response_payload["explanation_generation_mode"] = final_decision.get("explanation_generation_mode")
        response_payload["critic_failures"] = final_decision.get("critic_failures", [])

    response_payload.setdefault("policy_citations", final_decision.get("policy_citations", []))
    response_payload.setdefault("retrieval_evidence", final_decision.get("retrieval_evidence", []))
    response_payload.setdefault(
        "feature_attribution_summary",
        final_decision.get("feature_attribution_summary"),
    )
    response_payload.setdefault(
        "explanation_generation_mode",
        final_decision.get("explanation_generation_mode"),
    )
    response_payload.setdefault("critic_failures", final_decision.get("critic_failures", []))

    audit_narrative = build_audit_narrative(state, response_payload)
    audit_summary = {
        "policy_version": audit_narrative.get("policy_version"),
        "model_version": audit_narrative.get("model_version"),
        "prompt_version": audit_narrative.get("prompt_version"),
        "decision": audit_narrative.get("decision"),
        "risk_tier": audit_narrative.get("risk_tier"),
        "risk_score": audit_narrative.get("risk_score"),
        "triggered_reason_keys": audit_narrative.get("triggered_reason_keys", []),
    }
    response_payload["audit_summary"] = audit_summary

    if decision_type == "REFER_TO_HUMAN" and response_payload.get("review_packet"):
        response_payload["review_packet"]["audit_summary"] = audit_summary

    return {"final_response_payload": response_payload}
