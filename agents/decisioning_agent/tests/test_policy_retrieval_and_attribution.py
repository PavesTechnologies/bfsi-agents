import os

os.environ.setdefault("SERVICE_NAME", "decisioning_agent")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://test:test@localhost:5432/testdb")
os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("FORCE_DETERMINISTIC_EXPLANATIONS_ONLY", "true")

from src.domain.attribution.rule_attribution import build_rule_attribution
from src.domain.attribution.score_contribution import build_score_contribution
from src.domain.reason_codes.reason_types import ReasonSelectionContext
from src.domain.reason_codes.trigger_engine import evaluate_reason_triggers
from src.policy.policy_loader import load_underwriting_policy
from src.services.decision_model.explanation_service import build_cited_explanation
from src.services.policy_retrieval.retriever import retrieve_policy_evidence


def test_load_underwriting_policy_returns_typed_runtime_policy():
    policy = load_underwriting_policy()

    assert policy.bank.policy_version == "v2.0"
    assert policy.risk_weights.credit_score > 0
    assert policy.policy_citation.policy_id == "UPL_POLICY"


def test_trigger_engine_returns_auditable_candidates():
    candidates = evaluate_reason_triggers(
        ReasonSelectionContext(
            product_code="UNSECURED_PERSONAL_LOAN",
            aggregated_risk_tier="F",
            public_record_data={
                "bankruptcy_present": True,
                "years_since_bankruptcy": 1,
                "public_record_severity": "SEVERE",
            },
            income_data={"estimated_dti": 0.58, "income_missing_flag": False},
            behavior_data={"chargeoff_history": True, "behavior_risk": "POOR"},
            utilization_data={"utilization_risk": "HIGH", "utilization_ratio": 0.81},
            exposure_data={"exposure_risk": "HIGH"},
            inquiry_data={"inquiries_last_12m": 7},
            credit_score_data={"tradeline_count": 2, "credit_age_months": 12},
        )
    )

    reason_keys = [candidate.reason_key for candidate in candidates]
    assert "BANKRUPTCY_RECENT" in reason_keys
    assert "DTI_HIGH" in reason_keys
    assert all(candidate.citation_reference for candidate in candidates)


def test_policy_retrieval_returns_relevant_sections():
    evidence = retrieve_policy_evidence(
        reason_keys=["DTI_HIGH", "BANKRUPTCY_RECENT"],
        key_factors=["Debt-to-income ratio above policy threshold"],
    )

    section_ids = {item["section_id"] for item in evidence}
    assert "4.2" in section_ids or "5.1" in section_ids


def test_cited_explanation_falls_back_safely_and_includes_citations():
    result = build_cited_explanation(
        deterministic_outcome={
            "decision": "DECLINE",
            "primary_reason_key": "DTI_HIGH",
            "secondary_reason_key": "BANKRUPTCY_RECENT",
            "key_factors": ["Debt-to-income ratio above policy threshold"],
        }
    )

    assert result["generation_mode"] == "deterministic_fallback"
    assert result["cited_sections"]
    assert result["policy_evidence"]


def test_rule_and_score_attribution_are_human_readable():
    rule_attribution = build_rule_attribution(
        income_data={"estimated_dti": 0.58, "income_missing_flag": False},
        public_record_data={"bankruptcy_present": True, "years_since_bankruptcy": 1},
        utilization_data={"utilization_ratio": 0.8},
        exposure_data={"monthly_obligation_estimate": 2200},
        inquiry_data={"inquiries_last_12m": 6},
        behavior_data={"behavior_risk": "POOR"},
    )
    score_contribution = build_score_contribution(
        {"credit_score": 80, "public_record": 20},
        {"credit_score": 0.3, "public_record": 0.15},
    )

    assert any(item["rule"] == "dti_threshold" for item in rule_attribution)
    assert score_contribution[0]["contribution"] == 24.0
