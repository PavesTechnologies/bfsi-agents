from src.domain.decisioning.decision_engine import make_underwriting_decision
from src.domain.review.review_packet_builder import build_reviewer_packet
from src.domain.underwriting_models import UnderwritingResponse


def test_make_underwriting_decision_routes_to_human_review_when_income_missing():
    result = make_underwriting_decision(
        aggregated_risk_tier="C",
        credit_score_data={"base_limit_band": 35000, "score": 680, "score_band": "FAIR"},
        public_record_data={
            "bankruptcy_present": False,
            "years_since_bankruptcy": None,
            "public_record_severity": "NONE",
            "public_record_adjustment_factor": 1.0,
            "hard_decline_flag": False,
        },
        utilization_data={"utilization_adjustment_factor": 1.0, "utilization_risk": "GOOD", "utilization_ratio": 0.2},
        inquiry_data={"inquiry_penalty_factor": 1.0, "inquiries_last_12m": 1},
        income_data={"affordability_flag": False, "income_missing_flag": True, "estimated_dti": 99.9},
        behavior_data={"chargeoff_history": False, "behavior_risk": "FAIR"},
        exposure_data={"exposure_risk": "MODERATE"},
        user_request={"amount": 10000, "tenure": 24},
    )

    assert result.decision == "REFER_TO_HUMAN"
    assert result.primary_reason_key == "INCOME_UNVERIFIED"


def test_build_reviewer_packet_contains_summary_metrics():
    packet = build_reviewer_packet(
        application_id="APP-321",
        aggregated_risk_tier="D",
        aggregated_risk_score=44.5,
        credit_score_data={"score": 640, "score_band": "FAIR"},
        public_record_data={"public_record_severity": "LOW"},
        utilization_data={"utilization_ratio": 0.71},
        exposure_data={"exposure_risk": "HIGH"},
        inquiry_data={"inquiries_last_12m": 4},
        behavior_data={"behavior_risk": "FAIR"},
        income_data={"estimated_dti": 0.39, "income_missing_flag": False},
        user_request={"amount": 18000, "tenure": 24},
        final_decision={
            "reasoning_summary": "Borderline deterministic risk profile routed to human review.",
            "key_factors": ["Elevated credit utilization", "High existing debt obligations"],
            "reasoning_steps": ["step 1", "step 2"],
            "primary_reason_key": "UTILIZATION_HIGH",
            "secondary_reason_key": "EXPOSURE_HIGH",
        },
    )

    assert packet["recommended_action"] == "REFER_TO_HUMAN"
    assert packet["suggested_reason_keys"] == ["UTILIZATION_HIGH", "EXPOSURE_HIGH"]
    assert packet["metrics"]["exposure_risk"] == "HIGH"


def test_underwriting_response_accepts_human_review_payload():
    payload = {
        "application_id": "APP-321",
        "correlation_id": "REQ-321",
        "policy_version": "v2.0",
        "audit_summary": {
            "policy_version": "v2.0",
            "model_version": "openai/gpt-oss-120b",
            "prompt_version": "deterministic-underwriting-v1",
            "decision": "REFER_TO_HUMAN",
            "risk_tier": "D",
            "risk_score": 44.5,
            "triggered_reason_keys": ["UTILIZATION_HIGH", "EXPOSURE_HIGH"],
        },
        "decision": "REFER_TO_HUMAN",
        "risk_tier": "D",
        "risk_score": 44.5,
        "review_packet": {
            "application_id": "APP-321",
            "recommended_action": "REFER_TO_HUMAN",
            "summary": "Borderline deterministic risk profile routed to human review.",
            "requested_amount": 18000.0,
            "requested_tenure_months": 24,
            "risk_tier": "D",
            "risk_score": 44.5,
            "key_factors": ["Elevated credit utilization"],
            "reasoning_steps": ["step 1"],
            "suggested_reason_keys": ["UTILIZATION_HIGH", "EXPOSURE_HIGH"],
            "metrics": {"estimated_dti": 0.39},
            "audit_summary": {
                "policy_version": "v2.0",
                "model_version": "openai/gpt-oss-120b",
                "prompt_version": "deterministic-underwriting-v1",
                "decision": "REFER_TO_HUMAN",
                "risk_tier": "D",
                "risk_score": 44.5,
                "triggered_reason_keys": ["UTILIZATION_HIGH", "EXPOSURE_HIGH"],
            },
        },
        "original_decision_explanation": "Manual underwriting review is required for this borderline risk profile.",
        "primary_reason_key": "UTILIZATION_HIGH",
        "secondary_reason_key": "EXPOSURE_HIGH",
        "adverse_action_reasons": [
            {"reason_key": "UTILIZATION_HIGH", "reason_code": "UT01", "official_text": "Credit utilization too high"},
            {"reason_key": "EXPOSURE_HIGH", "reason_code": "EX01", "official_text": "Existing debt obligations are too high"},
        ],
        "reasoning_summary": "Deterministic decline reasons selected from triggered policy conditions.",
        "key_factors": ["Elevated credit utilization"],
    }

    response = UnderwritingResponse.model_validate(payload)

    assert response.decision == "REFER_TO_HUMAN"
    assert response.review_packet is not None
    assert response.audit_summary is not None
    assert response.review_packet.audit_summary is not None
