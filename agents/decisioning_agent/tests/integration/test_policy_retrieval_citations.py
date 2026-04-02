import os

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("FORCE_DETERMINISTIC_EXPLANATIONS_ONLY", "true")

from src.services.decision_model.explanation_service import build_cited_explanation


def test_policy_retrieval_citations_are_included_in_explanation_bundle():
    bundle = build_cited_explanation(
        deterministic_outcome={
            "decision": "DECLINE",
            "primary_reason_key": "DTI_HIGH",
            "secondary_reason_key": "BANKRUPTCY_RECENT",
            "key_factors": ["Debt-to-income ratio above policy threshold"],
        }
    )

    assert bundle["policy_evidence"]
    assert bundle["cited_sections"]
