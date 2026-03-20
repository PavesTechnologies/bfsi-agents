from src.services.receipt_builder import build_receipt
from src.services.transfer_state import (
    build_transfer_failure,
    build_transfer_result,
)


def test_build_transfer_result_marks_successful_transfer_as_disbursed():
    result = build_transfer_result(
        {
            "transaction_id": "TXN-123",
            "status": "SUCCESS",
            "timestamp": "2026-03-11 16:30:00",
        }
    )

    assert result["disbursement_status"] == "DISBURSED"
    assert result["transfer_status"] == "SUCCESS"
    assert result["reconciliation_required"] is False


def test_build_transfer_result_marks_pending_transfer_for_reconciliation():
    result = build_transfer_result(
        {
            "transaction_id": "TXN-456",
            "status": "PENDING",
            "timestamp": "2026-03-11 16:31:00",
        }
    )

    assert result["disbursement_status"] == "TRANSFER_PENDING"
    assert result["transfer_status"] == "PENDING"
    assert result["reconciliation_required"] is True


def test_build_transfer_failure_marks_failure_state():
    result = build_transfer_failure("Fund transfer failed: boom")

    assert result["disbursement_status"] == "FAILED"
    assert result["transfer_status"] == "FAILED"
    assert result["reconciliation_required"] is False


def test_build_receipt_includes_transfer_tracking_fields():
    state = {
        "application_id": "APP-123",
        "correlation_id": "REQ-123",
        "decision": "APPROVE",
        "disbursement_status": "TRANSFER_PENDING",
        "approved_amount": 100000.0,
        "disbursement_amount": 98000.0,
        "interest_rate": 12.5,
        "approved_tenure_months": 24,
        "monthly_emi": 4700.0,
        "total_interest": 12800.0,
        "total_repayment": 112800.0,
        "first_emi_date": "2026-04-11",
        "transaction_id": "TXN-123",
        "transfer_status": "PENDING",
        "transfer_timestamp": "2026-03-11 16:40:00",
        "reconciliation_required": True,
        "repayment_schedule": [
            {"installment_number": 1},
            {"installment_number": 2},
            {"installment_number": 3},
            {"installment_number": 24},
        ],
        "explanation": "Awaiting gateway settlement.",
    }

    result = build_receipt(state)

    assert result["correlation_id"] == "REQ-123"
    assert result["transfer_status"] == "PENDING"
    assert result["reconciliation_required"] is True
    assert len(result["schedule_preview"]) == 4
