"""
Node 1: Validate Decision

Validates that the incoming decision from the Decisioning Agent
is eligible for disbursement (APPROVE or accepted COUNTER_OFFER).
"""

from src.utils.audit_decorator import audit_node


@audit_node(agent_name="disbursement_agent")
def validate_decision_node(state: DisbursementState) -> dict:
    """
    Checks:
    1. Decision must be APPROVE or COUNTER_OFFER.
    2. For APPROVE: loan_details fields must be present.
    3. For COUNTER_OFFER: a selected_option_id must be provided
       and matched against the counter_offer options.
    """

    decision = state.get("decision", "")
    errors = []

    # ── DECLINE → reject immediately ──
    if decision == "DECLINE":
        return {
            "disbursement_status": "REJECTED",
            "validation_passed": False,
            "error": "Application was declined by the Decisioning Agent. Cannot disburse.",
        }

    # ── APPROVE path ──
    if decision == "APPROVE":
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
                "error": f"Validation failed for APPROVE: {'; '.join(errors)}",
            }

        return {
            "disbursement_status": "VALIDATED",
            "validation_passed": True,
        }

    # ── COUNTER_OFFER path ──
    if decision == "COUNTER_OFFER":
        counter_offer = state.get("counter_offer", {})
        selected_id = state.get("selected_option_id")

        if not selected_id:
            errors.append("Missing selected_option_id for counter offer acceptance")

        options = counter_offer.get("generated_options", [])
        matched_option = None
        for opt in options:
            if opt.get("option_id") == selected_id:
                matched_option = opt
                break

        if not matched_option and not errors:
            errors.append(f"selected_option_id '{selected_id}' not found in counter offer options")

        if errors:
            return {
                "disbursement_status": "FAILED",
                "validation_passed": False,
                "error": f"Validation failed for COUNTER_OFFER: {'; '.join(errors)}",
            }

        # Promote matched option fields into state for downstream nodes
        return {
            "disbursement_status": "VALIDATED",
            "validation_passed": True,
            "approved_amount": matched_option["proposed_amount"],
            "approved_tenure_months": matched_option["proposed_tenure_months"],
            "interest_rate": matched_option["proposed_interest_rate"],
            "disbursement_amount": matched_option["disbursement_amount"],
        }

    # ── Unknown decision type ──
    return {
        "disbursement_status": "FAILED",
        "validation_passed": False,
        "error": f"Unknown decision type: '{decision}'",
    }
