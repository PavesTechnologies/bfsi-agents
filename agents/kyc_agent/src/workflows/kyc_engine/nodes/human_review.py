"""
Human Review Node
"""

from src.core.telemetry import track_node
from src.workflows.kyc_engine.kyc_state import KYCState
from src.utils.audit_decorator import audit_node


@track_node("human_review")
@audit_node(agent_name="kyc_agent")
def human_review_node(state: KYCState) -> KYCState:
    # Placeholder: would integrate with Human UI system
    return {
        "human_review": {
            "reviewer_id": None,
            "decision": "PENDING",
            "reviewer_notes": "",
            "review_reason_codes": [],
        }
    }
