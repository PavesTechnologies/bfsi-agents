"""
Public Record Evaluation Engine
Bankruptcy / Liens / Hard Stop Detector
"""

from datetime import datetime

# from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState


# @track_node("public_record_engine")
def public_record_node(state: LoanApplicationState) -> LoanApplicationState:

    raw_experian = state.get("raw_experian_data") or {}

    public_record_data = {
        "bankruptcy_present": None,
        "years_since_bankruptcy": None,
        "public_record_severity": None,
        "public_record_adjustment_factor": None,
        "hard_decline_flag": None,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return {"public_record_data": public_record_data}