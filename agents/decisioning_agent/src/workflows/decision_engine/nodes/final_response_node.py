"""
Final Response Composer
LOS-Compatible Structured Output Builder
"""

from datetime import datetime

# from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState


# @track_node("final_response_engine")
def final_response_node(state: LoanApplicationState) -> LoanApplicationState:

    response_payload = {
        "application_id": state.get("application_id"),
        "decision": state.get("final_decision"),
        "counter_offer": state.get("counter_offer_data"),
        "aggregated_risk_tier": state.get("aggregated_risk_tier"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return {"final_response_payload": response_payload}