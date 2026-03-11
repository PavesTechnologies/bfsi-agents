from src.domain.underwriting_models import UnderwritingResponse


def test_underwriting_response_accepts_canonical_approve_payload():
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

    response = UnderwritingResponse.model_validate(payload)

    assert response.decision == "APPROVE"
    assert response.correlation_id == "REQ-123"
    assert response.risk_tier == "B"
    assert response.loan_details is not None
    assert response.loan_details.approved_tenure_months == 24
