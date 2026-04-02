"""Structured reviewer packet generation for underwriting HITL."""


def build_reviewer_packet(
    *,
    application_id: str,
    aggregated_risk_tier: str,
    aggregated_risk_score: float,
    credit_score_data: dict,
    public_record_data: dict,
    utilization_data: dict,
    exposure_data: dict,
    inquiry_data: dict,
    behavior_data: dict,
    income_data: dict,
    user_request: dict,
    final_decision: dict,
) -> dict:
    return {
        "application_id": application_id,
        "recommended_action": "REFER_TO_HUMAN",
        "summary": final_decision.get("reasoning_summary") or final_decision.get("explanation"),
        "requested_amount": float(user_request.get("amount", 0) or 0),
        "requested_tenure_months": int(user_request.get("tenure", 0) or 0),
        "risk_tier": aggregated_risk_tier,
        "risk_score": aggregated_risk_score,
        "key_factors": final_decision.get("key_factors", []),
        "reasoning_steps": final_decision.get("reasoning_steps", []),
        "suggested_reason_keys": [
            key
            for key in [
                final_decision.get("primary_reason_key"),
                final_decision.get("secondary_reason_key"),
            ]
            if key
        ],
        "candidate_reason_codes": final_decision.get("candidate_reason_codes", []),
        "policy_citations": final_decision.get("policy_citations", []),
        "feature_attribution_summary": final_decision.get("feature_attribution_summary", {}),
        "metrics": {
            "credit_score": credit_score_data.get("score"),
            "score_band": credit_score_data.get("score_band"),
            "estimated_dti": income_data.get("estimated_dti"),
            "income_missing_flag": income_data.get("income_missing_flag"),
            "public_record_severity": public_record_data.get("public_record_severity"),
            "utilization_ratio": utilization_data.get("utilization_ratio"),
            "exposure_risk": exposure_data.get("exposure_risk"),
            "inquiries_last_12m": inquiry_data.get("inquiries_last_12m"),
            "behavior_risk": behavior_data.get("behavior_risk"),
        },
    }
