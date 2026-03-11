from src.services.disbursement_transitions import derive_transition_history


def test_derive_transition_history_for_successful_disbursement():
    state = {
        "decision": "APPROVE",
        "risk_tier": "B",
        "validation_passed": True,
        "repayment_schedule": [{"installment_number": 1}, {"installment_number": 2}],
        "monthly_emi": 4200.0,
        "transaction_id": "TXN-123",
        "transfer_status": "SUCCESS",
        "reconciliation_required": False,
        "disbursement_status": "DISBURSED",
        "explanation": "Funds settled successfully.",
    }

    history = derive_transition_history(state)

    assert [item["to_status"] for item in history] == [
        "PENDING",
        "VALIDATED",
        "SCHEDULED",
        "TRANSFER_INITIATED",
        "DISBURSED",
    ]


def test_derive_transition_history_for_pending_reconciliation():
    state = {
        "decision": "APPROVE",
        "risk_tier": "A",
        "validation_passed": True,
        "repayment_schedule": [{"installment_number": 1}],
        "monthly_emi": 8000.0,
        "transaction_id": "TXN-999",
        "transfer_status": "PENDING",
        "reconciliation_required": True,
        "disbursement_status": "TRANSFER_PENDING",
        "explanation": "Awaiting settlement.",
    }

    history = derive_transition_history(state)

    assert history[-1]["to_status"] == "TRANSFER_PENDING"
    assert history[-1]["transition_metadata"]["reconciliation_required"] is True


def test_derive_transition_history_for_validation_failure():
    state = {
        "validation_passed": False,
        "disbursement_status": "REJECTED",
        "error": "Application was declined by the Decisioning Agent. Cannot disburse.",
    }

    history = derive_transition_history(state)

    assert [item["to_status"] for item in history] == ["PENDING", "REJECTED"]
    assert history[-1]["reason"] == state["error"]
