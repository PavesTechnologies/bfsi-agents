"""Export helpers for underwriting monitoring telemetry."""

from decimal import Decimal
from typing import Any, Dict

from src.services.monitoring.decision_metrics import build_decision_telemetry


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def export_underwriting_decision_metrics(
    decision_record: Any,
    *,
    evaluation_attributes: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Convert a persisted underwriting record into a telemetry payload."""
    final_decision = {
        "application_id": getattr(decision_record, "application_id", None),
        "policy_version": getattr(decision_record, "policy_version", None),
        "decision": getattr(decision_record, "decision", None),
        "risk_tier": getattr(decision_record, "risk_tier", None),
        "risk_score": _as_float(getattr(decision_record, "risk_score", None)),
        "primary_reason_key": getattr(decision_record, "primary_reason_key", None),
        "secondary_reason_key": getattr(decision_record, "secondary_reason_key", None),
        "loan_details": {
            "approved_amount": _as_float(getattr(decision_record, "approved_amount", None)),
        },
        "counter_offer": getattr(decision_record, "counter_offer_data", None),
        "review_packet": (getattr(decision_record, "raw_decision_payload", None) or {}).get("human_review_packet")
        or (getattr(decision_record, "raw_decision_payload", None) or {}).get("final_response_payload", {}).get("review_packet"),
        "audit_summary": {
            "model_version": getattr(decision_record, "model_version", None),
            "prompt_version": getattr(decision_record, "prompt_version", None),
            "triggered_reason_keys": (
                (getattr(decision_record, "audit_narrative", None) or {}).get("triggered_reason_keys", [])
            ),
        },
    }

    return build_decision_telemetry(
        final_decision=final_decision,
        audit_narrative=getattr(decision_record, "audit_narrative", None) or {},
        evaluation_attributes=evaluation_attributes,
    )
