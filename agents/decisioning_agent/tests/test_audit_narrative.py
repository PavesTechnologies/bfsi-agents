from src.domain.audit.narrative_builder import build_audit_narrative
from src.repositories.underwriting_repository import UnderwritingRepository


def test_build_audit_narrative_includes_versions_and_calculations():
    state = {
        "application_id": "APP-777",
        "policy_metadata": {"policy_version": "v2.0"},
        "version_metadata": {
            "model_version": "openai/gpt-oss-120b",
            "prompt_version": "deterministic-underwriting-v1",
        },
        "aggregated_risk_tier": "F",
        "aggregated_risk_score": 12.5,
        "user_request": {"amount": 10000, "tenure": 24},
        "income_data": {"estimated_dti": 0.52, "affordability_flag": False},
        "utilization_data": {"utilization_ratio": 0.81},
        "exposure_data": {"monthly_obligation_estimate": 2100},
        "credit_score_data": {"score": 620},
        "final_decision": {"approved_amount": 0},
        "decision_result": {"decision": "DECLINE"},
        "parallel_tasks_completed": ["credit_score_engine", "income_engine"],
    }
    final_response = {
        "decision": "DECLINE",
        "primary_reason_key": "DTI_HIGH",
        "secondary_reason_key": "EXPOSURE_HIGH",
        "key_factors": ["Debt-to-income ratio above policy threshold"],
    }

    narrative = build_audit_narrative(state, final_response)

    assert narrative["policy_version"] == "v2.0"
    assert narrative["model_version"] == "openai/gpt-oss-120b"
    assert narrative["prompt_version"] == "deterministic-underwriting-v1"
    assert narrative["calculations"]["estimated_dti"] == 0.52
    assert narrative["triggered_reason_keys"] == ["DTI_HIGH", "EXPOSURE_HIGH"]


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        self.commits += 1


import pytest


@pytest.mark.anyio
async def test_underwriting_repository_persists_version_fields_and_audit_narrative():
    session = FakeSession()
    repo = UnderwritingRepository(session)

    await repo.save_decision(
        application_id="APP-777",
        decision="DECLINE",
        final_decision={
            "decision": "DECLINE",
            "decline_reason": "Debt-to-income ratio too high",
            "primary_reason_key": "DTI_HIGH",
            "secondary_reason_key": "EXPOSURE_HIGH",
            "adverse_action_reasons": [],
            "reasoning_steps": ["step 1"],
        },
        aggregated_risk_score=12.5,
        aggregated_risk_tier="F",
        policy_version="v2.0",
        model_version="openai/gpt-oss-120b",
        prompt_version="deterministic-underwriting-v1",
        audit_narrative={"application_id": "APP-777", "decision": "DECLINE"},
    )

    saved = session.added[0]
    assert saved.policy_version == "v2.0"
    assert saved.model_version == "openai/gpt-oss-120b"
    assert saved.prompt_version == "deterministic-underwriting-v1"
    assert saved.audit_narrative["decision"] == "DECLINE"
