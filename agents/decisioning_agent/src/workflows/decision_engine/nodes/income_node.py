"""
Income & Affordability Engine
DTI & EMI Capacity Evaluator
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState


@track_node("income_engine")
def income_node(state: LoanApplicationState) -> LoanApplicationState:

    income_data = {
        "estimated_dti": None,
        "income_risk": None,
        "affordability_flag": None,
        "income_missing_flag": None,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return {"income_data": income_data}