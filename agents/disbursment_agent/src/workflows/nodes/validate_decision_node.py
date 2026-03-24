"""
Node 1: Validate Decision

Validates that the incoming request contains all required loan terms
before proceeding with schedule generation and fund transfer.
The caller is responsible for resolving the decision — disbursement
only processes pre-approved loan terms.
"""

from src.workflows.state import DisbursementState
from src.utils.audit_decorator import audit_node


@audit_node(agent_name="disbursement_agent")
def validate_decision_node(state: DisbursementState) -> dict:
    """
    Validates that all four required loan term fields are present and non-zero.
    """
    errors = []

    if not state.get("approved_amount"):
        errors.append("Missing approved_amount")
    if not state.get("approved_tenure_months"):
        errors.append("Missing approved_tenure_months")
    if state.get("interest_rate") is None:
        errors.append("Missing interest_rate")
    if not state.get("disbursement_amount"):
        errors.append("Missing disbursement_amount")

    if errors:
        return {
            "disbursement_status": "FAILED",
            "validation_passed": False,
            "error": f"Validation failed: {'; '.join(errors)}",
        }

    return {
        "disbursement_status": "VALIDATED",
        "validation_passed": True,
    }