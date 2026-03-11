from src.domain.entities import DisbursementRequest


def test_disbursement_request_accepts_decisioning_approve_payload():
    payload = {
        "application_id": "APP-123",
        "correlation_id": "REQ-123",
        "decision": "APPROVE",
        "risk_tier": "B",
        "risk_score": 72.4,
        "timestamp": "2026-03-11 12:00:00",
        "loan_details": {
            "approved_amount": 10000.0,
            "approved_tenure_months": 24,
            "interest_rate": 12.5,
            "disbursement_amount": 9800.0,
            "explanation": "Approved within policy thresholds.",
        },
    }

    request = DisbursementRequest.model_validate(payload)

    assert request.decision == "APPROVE"
    assert request.correlation_id == "REQ-123"
    assert request.risk_tier == "B"
    assert request.loan_details is not None
    assert request.loan_details.disbursement_amount == 9800.0
