"""
Underwriting Service

Entry point for running the decisioning workflow.
Accepts an UnderwritingRequest and returns the final decision payload.
"""

from src.workflows.decision_flow import build_underwriting_graph
from src.domain.underwriting_models import UnderwritingRequest
from datetime import datetime


_graph = build_underwriting_graph()


def run_underwriting(request: UnderwritingRequest) -> dict:
    """
    Execute the underwriting decision workflow.

    Args:
        request: An UnderwritingRequest containing applicant, credit,
                 and financial data for risk evaluation.

    Returns:
        The final decision response payload as a dict.
    """

    # ─── Build initial state from the request ───
    initial_state = {
        "application_id": request.application_id,
        "raw_experian_data": request.raw_experian_data,
        "user_request": {
            "amount": request.requested_amount,
            "tenure": request.requested_tenure_months,
        },
        "bank_statement_summary": {
            "monthly_income": request.monthly_income,
        },
    }

    # ─── Run the graph ───
    final_state = _graph.invoke(initial_state)

    final_payload = final_state.get("final_response_payload")
    if final_payload:
        result = dict(final_payload)
        result.setdefault("application_id", final_state.get("application_id"))
        result.setdefault("timestamp", datetime.now().isoformat())
    else:
        final_decision = final_state.get("final_decision") or {}
        counter_offer_data = final_state.get("counter_offer_data")
        result = {
            "application_id": final_state.get("application_id"),
            "aggregated_risk_tier": final_state.get("aggregated_risk_tier"),
            "aggregated_risk_score": final_state.get("aggregated_risk_score"),
            "decision": final_decision.get("decision"),
            "timestamp": datetime.now().isoformat(),
        }

        decision = final_decision.get("decision")
        if decision == "APPROVE":
            result["loan_details"] = {
                "approved_amount": final_decision.get("approved_amount"),
                "approved_tenure_months": final_decision.get("approved_tenure"),
                "interest_rate": final_decision.get("interest_rate"),
                "disbursement_amount": final_decision.get("disbursement_amount"),
                "explanation": final_decision.get("explanation"),
            }
        elif decision == "COUNTER_OFFER":
            result["counter_offer"] = counter_offer_data
            result["original_decision_explanation"] = final_decision.get(
                "explanation"
            )
        elif decision == "DECLINE":
            result["decline_reason"] = final_decision.get("explanation")
            result["reasoning_steps"] = final_decision.get("reasoning_steps", [])

    print("Graph execution result Underwriting:", result )
    return result
