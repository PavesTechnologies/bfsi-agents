import os

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ["FORCE_DETERMINISTIC_EXPLANATIONS_ONLY"] = "true"

from src.services.decision_model.explanation_service import build_cited_explanation


def test_kill_switch_forces_deterministic_explanation_mode():
    result = build_cited_explanation(
        deterministic_outcome={
            "decision": "APPROVE",
            "primary_reason_key": None,
            "secondary_reason_key": None,
            "key_factors": [],
        }
    )

    assert result["generation_mode"] == "deterministic_fallback"
