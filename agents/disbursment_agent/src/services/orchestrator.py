"""
Workflow Orchestrator

Entry point for running the disbursement workflow.
Accepts a DisbursementRequest and returns the final receipt.
"""

from src.workflows.decision_flow import build_disbursement_graph
from src.domain.entities import DisbursementRequest

_graph = build_disbursement_graph()


def run_disbursement(request: DisbursementRequest) -> dict:
    """
    Execute the disbursement workflow.

    Args:
        request: A DisbursementRequest containing the decisioning agent's output.

    Returns:
        The final disbursement receipt as a dict.
    """

    # ─── Build initial state from the request ───
    initial_state = {
        "application_id": request.application_id,
        "decision": request.decision,
        "risk_tier": request.aggregated_risk_tier,
        "risk_score": request.aggregated_risk_score,
        "disbursement_status": "PENDING",
    }

    # ─── APPROVE path: extract loan details ───
    if request.decision == "APPROVE" and request.loan_details:
        initial_state["approved_amount"] = request.loan_details.get("approved_amount")
        initial_state["approved_tenure_months"] = request.loan_details.get("approved_tenure_months")
        initial_state["interest_rate"] = request.loan_details.get("interest_rate")
        initial_state["disbursement_amount"] = request.loan_details.get("disbursement_amount")
        initial_state["explanation"] = request.loan_details.get("explanation")

    # ─── COUNTER_OFFER path: pass counter offer + selected option ───
    elif request.decision == "COUNTER_OFFER" and request.counter_offer:
        initial_state["counter_offer"] = request.counter_offer
        initial_state["selected_option_id"] = request.selected_option_id

    # ─── DECLINE path: just pass decline reason ───
    elif request.decision == "DECLINE":
        initial_state["explanation"] = request.decline_reason

    # ─── Run the graph ───
    final_state = _graph.invoke(initial_state)

    return final_state.get("disbursement_receipt", {})
