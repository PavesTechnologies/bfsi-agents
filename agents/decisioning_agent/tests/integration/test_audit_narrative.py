import os

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")

from src.domain.audit.narrative_builder import build_audit_narrative


def test_audit_narrative_contains_citations_and_attribution():
    narrative = build_audit_narrative(
        {
            "application_id": "APP-1",
            "policy_metadata": {"id": "BANK_A", "policy_version": "v2.0"},
            "version_metadata": {"model_version": "openai/gpt-oss-120b", "prompt_version": "deterministic-underwriting-v1"},
            "aggregated_risk_tier": "F",
            "aggregated_risk_score": 10.0,
            "user_request": {"amount": 10000, "tenure": 24},
            "income_data": {"estimated_dti": 0.5, "affordability_flag": False},
            "utilization_data": {"utilization_ratio": 0.8},
            "exposure_data": {"monthly_obligation_estimate": 2100},
            "credit_score_data": {"score": 620},
            "final_decision": {"approved_amount": 0},
            "decision_result": {"decision": "DECLINE"},
            "parallel_tasks_completed": ["credit_score", "income"],
        },
        {
            "decision": "DECLINE",
            "primary_reason_key": "DTI_HIGH",
            "secondary_reason_key": "BANKRUPTCY_RECENT",
            "candidate_reason_codes": [{"reason_key": "DTI_HIGH"}],
            "selected_reason_codes": [{"reason_key": "DTI_HIGH"}, {"reason_key": "BANKRUPTCY_RECENT"}],
            "policy_citations": [{"section_id": "4.2"}],
            "retrieval_evidence": [{"section_id": "4.2"}],
            "feature_attribution_summary": {"rule_attribution": [{"rule": "dti_threshold"}]},
        },
    )

    assert narrative["policy_citations"]
    assert narrative["feature_attribution_summary"]["rule_attribution"]
