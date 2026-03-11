"""
Explanation Node
"""

from src.core.telemetry import track_node
from src.workflows.kyc_engine.kyc_state import KYCState
from src.utils.audit_decorator import audit_node


@track_node("explanation")
@audit_node(agent_name="kyc_agent")
def explanation_node(state: KYCState) -> KYCState:
    decision = state.get("risk_decision", {})

    if decision.get("final_status") == "PASS":
        return {
            "decision_explanation": "KYC Decision: PASS - No further action required."
        }

    triggered_rule = decision.get("triggered_rules")
    reason = f"Triggered Rule: {triggered_rule}"

    explanation = f"KYC Decision: {decision.get('final_status')} - {reason}"

    return {"decision_explanation": explanation}
