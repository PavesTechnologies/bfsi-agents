import os

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")

from src.services.validation.explanation_critic import critique_explanation


def test_explanation_critic_flags_missing_evidence_sections():
    result = critique_explanation(
        explanation_text="Declined because DTI was too high.",
        reason_keys=["DTI_HIGH"],
        cited_sections=["4.2"],
        policy_evidence=[],
    )

    assert result["passed"] is False
    assert result["failures"]
