from src.workflows.state import DisbursementState


def derive_transition_history(state: DisbursementState) -> list[dict]:
    history: list[dict] = [
        {
            "from_status": None,
            "to_status": "PENDING",
            "reason": "Disbursement request accepted for processing.",
            "transition_metadata": {},
        }
    ]

    if state.get("validation_passed"):
        history.append(
            {
                "from_status": "PENDING",
                "to_status": "VALIDATED",
                "reason": "Decision payload passed disbursement validation.",
                "transition_metadata": {
                    "decision": state.get("decision"),
                    "risk_tier": state.get("risk_tier"),
                },
            }
        )

        if state.get("repayment_schedule"):
            history.append(
                {
                    "from_status": "VALIDATED",
                    "to_status": "SCHEDULED",
                    "reason": "Repayment schedule generated.",
                    "transition_metadata": {
                        "installment_count": len(state.get("repayment_schedule", [])),
                        "monthly_emi": state.get("monthly_emi"),
                    },
                }
            )

        if state.get("transaction_id"):
            history.append(
                {
                    "from_status": "SCHEDULED",
                    "to_status": "TRANSFER_INITIATED",
                    "reason": "Fund transfer submitted to gateway.",
                    "transition_metadata": {
                        "transaction_id": state.get("transaction_id"),
                        "transfer_status": state.get("transfer_status"),
                    },
                }
            )

    final_status = state.get("disbursement_status")
    if final_status and final_status not in {"PENDING", "VALIDATED", "SCHEDULED", "TRANSFER_INITIATED"}:
        previous_status = history[-1]["to_status"] if history else None
        history.append(
            {
                "from_status": previous_status,
                "to_status": final_status,
                "reason": state.get("error") or state.get("explanation"),
                "transition_metadata": {
                    "reconciliation_required": state.get("reconciliation_required", False),
                    "transfer_status": state.get("transfer_status"),
                },
            }
        )

    return history
