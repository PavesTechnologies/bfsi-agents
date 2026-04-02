"""Builders for normalized underwriting audit narratives."""

from src.domain.audit.audit_narrative import UnderwritingAuditNarrative


def build_audit_narrative(state: dict, final_response_payload: dict) -> UnderwritingAuditNarrative:
    final_decision = state.get("final_decision", {})
    user_request = state.get("user_request", {})
    income_data = state.get("income_data", {})
    utilization_data = state.get("utilization_data", {})
    exposure_data = state.get("exposure_data", {})
    credit_score_data = state.get("credit_score_data", {})
    policy_metadata = state.get("policy_metadata", {})
    version_metadata = state.get("version_metadata", {})

    triggered_reason_keys = [
        key
        for key in [
            final_response_payload.get("primary_reason_key"),
            final_response_payload.get("secondary_reason_key"),
        ]
        if key
    ]

    return {
        "application_id": state.get("application_id"),
        "decision": final_response_payload.get("decision"),
        "policy_id": policy_metadata.get("id"),
        "policy_version": policy_metadata.get("policy_version"),
        "model_version": version_metadata.get("model_version"),
        "prompt_version": version_metadata.get("prompt_version"),
        "risk_tier": state.get("aggregated_risk_tier"),
        "risk_score": state.get("aggregated_risk_score"),
        "requested_amount": float(user_request.get("amount", 0) or 0),
        "requested_tenure_months": int(user_request.get("tenure", 0) or 0),
        "key_factors": final_response_payload.get("key_factors", []),
        "triggered_reason_keys": triggered_reason_keys,
        "candidate_reason_codes": final_response_payload.get("candidate_reason_codes", []),
        "selected_reason_codes": final_response_payload.get("selected_reason_codes", []),
        "policy_citations": final_response_payload.get("policy_citations", []),
        "retrieval_evidence": final_response_payload.get("retrieval_evidence", []),
        "feature_attribution_summary": final_response_payload.get("feature_attribution_summary", {}),
        "calculations": {
            "estimated_dti": income_data.get("estimated_dti"),
            "affordability_flag": income_data.get("affordability_flag"),
            "utilization_ratio": utilization_data.get("utilization_ratio"),
            "monthly_obligation_estimate": exposure_data.get("monthly_obligation_estimate"),
            "credit_score": credit_score_data.get("score"),
            "approved_amount": final_decision.get("approved_amount"),
        },
        "decision_path": [
            "pi_deletion",
            "parallel_risk_nodes",
            "aggregate",
            "decision",
            (
                "human_review_packet"
                if final_response_payload.get("decision") == "REFER_TO_HUMAN"
                else "counter_offer"
                if final_response_payload.get("decision") == "COUNTER_OFFER"
                else "final_response"
            ),
        ],
        "human_review_required": final_response_payload.get("decision") == "REFER_TO_HUMAN",
        "human_review_outcome": None,
        "routing": {
            "decision_result": state.get("decision_result", {}),
            "parallel_tasks_completed": state.get("parallel_tasks_completed", []),
        },
    }
