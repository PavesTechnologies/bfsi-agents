"""
Explanation Node
"""

from src.core.telemetry import track_node
from src.workflows.kyc_engine.kyc_state import KYCState


@track_node("explanation")
def explanation_node(state: KYCState) -> KYCState:
    decision = state.get("risk_decision", {})
    reason = decision.get("decision_reason", "No reason provided")

    explanation = f"KYC Decision: {decision.get('final_status')} - {reason}"

    return {"decision_explanation": explanation}
