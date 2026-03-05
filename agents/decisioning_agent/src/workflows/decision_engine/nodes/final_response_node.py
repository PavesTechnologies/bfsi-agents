"""
Final Response Composer
LOS-Compatible Structured Output Builder
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState


@track_node("final_response_engine")
def final_response_node(state: LoanApplicationState) -> LoanApplicationState:

    final_decision = state.get("final_decision", {})
    counter_offer = state.get("counter_offer_data")
    decision_type = final_decision.get("decision", "UNKNOWN")

    # ==================================================
    # Build the structured response payload
    # ==================================================
    response_payload = {
        "application_id": state.get("application_id"),
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

    elif decision_type == "DECLINE":
        response_payload["decline_reason"] = final_decision.get("explanation")
        response_payload["reasoning_steps"] = final_decision.get("reasoning_steps", [])

    return {"final_response_payload": response_payload}