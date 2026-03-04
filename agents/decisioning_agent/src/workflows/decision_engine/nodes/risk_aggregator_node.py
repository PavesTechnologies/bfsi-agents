"""
Underwriting Risk Aggregation Engine
Policy-Driven, Auditable Decision Core
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState


@track_node("underwriting_risk_aggregator")
def risk_aggregator_node(state: LoanApplicationState) -> LoanApplicationState:

    # ==================================================
    # 1️⃣ Extract Signals
    # ==================================================
    signals = {
        "credit_score": state.get("credit_score_data"),
        "public_record": state.get("public_record_data"),
        "utilization": state.get("utilization_data"),
        "exposure": state.get("exposure_data"),
        "behavior": state.get("behavior_data"),
        "inquiry": state.get("inquiry_data"),
        "income": state.get("income_data"),
    }

    # ==================================================
    # 2️⃣ Aggregation Placeholder
    # ==================================================
    aggregated_risk_score = None
    aggregated_risk_tier = None

    reasoning_trace = {
        "signals": signals,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return {
        "aggregated_risk_score": aggregated_risk_score,
        "aggregated_risk_tier": aggregated_risk_tier,
        "reasoning_trace": reasoning_trace,
    }