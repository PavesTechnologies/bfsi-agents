"""
Debt Exposure Engine
Outstanding Liability Evaluator
"""

from datetime import datetime

# from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState


# @track_node("exposure_engine")
def exposure_node(state: LoanApplicationState) -> LoanApplicationState:

    exposure_data = {
        "total_existing_debt": None,
        "monthly_obligation_estimate": None,
        "exposure_risk": None,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return {"exposure_data": exposure_data}