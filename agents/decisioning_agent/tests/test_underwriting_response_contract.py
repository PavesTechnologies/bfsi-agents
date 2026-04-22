from src.domain.underwriting_models import UnderwritingResponse


def test_underwriting_response_accepts_canonical_approve_payload():
    payload = {
        "application_id": "APP-123",
        "correlation_id": "REQ-123",
        "audit_summary": {
            "policy_version": "v2.0",
            "model_version": "openai/gpt-oss-120b",
            "prompt_version": "deterministic-underwriting-v1",
            "decision": "APPROVE",
            "risk_tier": "B",
            "risk_score": 72.4,
            "triggered_reason_keys": [],
        },
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
    assert response.audit_summary is not None
    assert response.loan_details is not None
    assert response.loan_details.approved_tenure_months == 24


def test_underwriting_response_accepts_canonical_decline_payload():
    payload = {
        "application_id": "APP-456",
        "correlation_id": "REQ-456",
        "policy_version": "v2.0",
        "audit_summary": {
            "policy_version": "v2.0",
            "model_version": "openai/gpt-oss-120b",
            "prompt_version": "deterministic-underwriting-v1",
            "decision": "DECLINE",
            "risk_tier": "F",
            "risk_score": 12.7,
            "triggered_reason_keys": ["BANKRUPTCY_RECENT", "DTI_HIGH"],
        },
        "decision": "DECLINE",
        "risk_tier": "F",
        "risk_score": 12.7,
        "timestamp": "2026-04-01 12:00:00",
        "decline_reason": "Recent bankruptcy on file",
        "primary_reason_key": "BANKRUPTCY_RECENT",
        "secondary_reason_key": "DTI_HIGH",
        "adverse_action_reasons": [
            {
                "reason_key": "BANKRUPTCY_RECENT",
                "reason_code": "PR01",
                "official_text": "Recent bankruptcy on file",
            },
            {
                "reason_key": "DTI_HIGH",
                "reason_code": "01",
                "official_text": "Debt-to-income ratio too high",
            },
        ],
        "adverse_action_notice": "Recent bankruptcy on file; Debt-to-income ratio too high",
        "reasoning_summary": "Deterministic decline reasons selected from triggered policy conditions.",
        "key_factors": [
            "Hard decline public-record trigger",
            "Debt-to-income ratio above policy threshold",
        ],
        "reasoning_steps": [
            "Aggregated risk tier evaluated as F.",
            "Hard decline conditions were met.",
        ],
    }

    response = UnderwritingResponse.model_validate(payload)

    assert response.decision == "DECLINE"
    assert response.policy_version == "v2.0"
    assert response.audit_summary is not None
    assert response.primary_reason_key == "BANKRUPTCY_RECENT"
    assert response.secondary_reason_key == "DTI_HIGH"
    assert response.adverse_action_notice is not None
    assert response.key_factors is not None


def test_underwriting_response_accepts_counter_offer_maximum_approved_amount():
    payload = {
        "application_id": "APP-789",
        "correlation_id": "REQ-789",
        "policy_version": "v2.0",
        "decision": "COUNTER_OFFER",
        "risk_tier": "A",
        "risk_score": 88.0,
        "timestamp": "2026-04-22 12:00:00",
        "maximum_approved_amount": 60000.0,
        "counter_offer": {
            "original_request_dti": 0.28,
            "max_affordable_emi": 12500.0,
            "counter_offer_logic": "Alternatives generated from deterministic affordability constraints.",
            "generated_options": [
                {
                    "option_id": "OPT_REDUCED_AMOUNT",
                    "description": "Reduce principal while keeping the requested tenure.",
                    "proposed_amount": 60000.0,
                    "proposed_tenure_months": 24,
                    "proposed_interest_rate": 7.5,
                    "disbursement_amount": 58800.0,
                    "monthly_payment_emi": 2700.0,
                    "total_repayment": 64800.0,
                }
            ],
            "confidence_score": 1.0,
            "timestamp": "2026-04-22 12:00:00",
        },
        "original_decision_explanation": "A counter offer was generated because the requested amount exceeded deterministic lending capacity.",
    }

    response = UnderwritingResponse.model_validate(payload)

    assert response.decision == "COUNTER_OFFER"
    assert response.maximum_approved_amount == 60000.0
    assert response.counter_offer is not None
