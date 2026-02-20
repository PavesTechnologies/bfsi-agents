"""
Human Review Node
"""

from src.workflows.kyc_engine.kyc_state import KYCState


def human_review_node(state: KYCState) -> KYCState:
    # Placeholder: would integrate with Human UI system
    return {
        "human_review": {
            "reviewer_id": None,
            "decision": "PENDING",
            "reviewer_notes": "",
            "review_reason_codes": []
        }
    }