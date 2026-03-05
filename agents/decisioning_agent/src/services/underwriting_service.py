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

    result =  {
        "application_id": final_state.get("application_id"),
        "aggregated_risk_tier": final_state.get("aggregated_risk_tier"),
        "aggregated_risk_score": final_state.get("aggregated_risk_score"),
        "decision": final_state.get("final_decision").get("decision"),
        "timestamp": datetime.now().isoformat(),
    }

    print("Graph execution result Underwriting:", result )
    return result
