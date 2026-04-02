"""Decision telemetry builders for monitoring and fairness analysis."""

from typing import Any, Dict


POSITIVE_DECISIONS = {"APPROVE"}
REVIEW_DECISIONS = {"REFER_TO_HUMAN"}


def build_decision_telemetry(
    *,
    final_decision: Dict[str, Any],
    audit_narrative: Dict[str, Any] | None = None,
    evaluation_attributes: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Normalize an underwriting outcome into a monitoring-friendly record."""
    audit_narrative = audit_narrative or {}
    evaluation_attributes = evaluation_attributes or {}

    decision = final_decision.get("decision", "UNKNOWN")
    counter_offer = final_decision.get("counter_offer") or {}
    loan_details = final_decision.get("loan_details") or {}

    return {
        "application_id": final_decision.get("application_id") or audit_narrative.get("application_id"),
        "decision": decision,
        "decision_group": (
            "positive"
            if decision in POSITIVE_DECISIONS
            else "manual_review"
            if decision in REVIEW_DECISIONS
            else "negative"
        ),
        "is_approved": decision in POSITIVE_DECISIONS,
        "is_counter_offer": decision == "COUNTER_OFFER",
        "is_manual_review": decision in REVIEW_DECISIONS,
        "risk_tier": final_decision.get("risk_tier") or audit_narrative.get("risk_tier"),
        "risk_score": final_decision.get("risk_score") or audit_narrative.get("risk_score"),
        "policy_version": final_decision.get("policy_version") or audit_narrative.get("policy_version"),
        "model_version": (
            (final_decision.get("audit_summary") or {}).get("model_version")
            or audit_narrative.get("model_version")
        ),
        "prompt_version": (
            (final_decision.get("audit_summary") or {}).get("prompt_version")
            or audit_narrative.get("prompt_version")
        ),
        "triggered_reason_keys": (
            final_decision.get("audit_summary", {}).get("triggered_reason_keys")
            or audit_narrative.get("triggered_reason_keys", [])
        ),
        "primary_reason_key": final_decision.get("primary_reason_key"),
        "secondary_reason_key": final_decision.get("secondary_reason_key"),
        "approved_amount": loan_details.get("approved_amount"),
        "counter_offer_option_count": len(counter_offer.get("generated_options", [])),
        "review_reason_count": len((final_decision.get("review_packet") or {}).get("suggested_reason_keys", [])),
        "evaluation_attributes": evaluation_attributes,
    }
