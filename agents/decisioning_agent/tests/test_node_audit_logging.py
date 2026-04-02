import pytest

from src.models.node_audit import NodeAuditLog
from src.repositories.audit_repository import AuditRepository
from src.utils.audit_decorator import build_state_summary


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        self.commits += 1


def test_build_state_summary_extracts_compliance_friendly_fields():
    summary = build_state_summary(
        {
            "application_id": "APP-900",
            "correlation_id": "REQ-900",
            "policy_metadata": {"policy_version": "v2.0"},
            "version_metadata": {
                "model_version": "openai/gpt-oss-120b",
                "prompt_version": "deterministic-underwriting-v1",
            },
            "aggregated_risk_tier": "F",
            "aggregated_risk_score": 11.2,
            "parallel_tasks_completed": ["income_engine", "decision_engine"],
            "final_decision": {
                "decision": "DECLINE",
                "primary_reason_key": "DTI_HIGH",
                "secondary_reason_key": "EXPOSURE_HIGH",
            },
        }
    )

    assert summary is not None
    assert summary["application_id"] == "APP-900"
    assert summary["policy_version"] == "v2.0"
    assert summary["model_version"] == "openai/gpt-oss-120b"
    assert summary["prompt_version"] == "deterministic-underwriting-v1"
    assert summary["decision"] == "DECLINE"
    assert summary["triggered_reason_keys"] == ["DTI_HIGH", "EXPOSURE_HIGH"]
    assert "final_decision" in summary["state_keys"]


@pytest.mark.anyio
async def test_audit_repository_persists_input_and_output_summaries():
    session = FakeSession()
    repo = AuditRepository(session)

    await repo.save_node_log(
        application_id="APP-900",
        agent_name="decisioning_agent",
        node_name="final_response_node",
        input_state={"application_id": "APP-900"},
        input_summary={"application_id": "APP-900", "decision": "DECLINE"},
        output_summary={"application_id": "APP-900", "decision": "DECLINE"},
        output_state={"final_response_payload": {"application_id": "APP-900", "decision": "DECLINE"}},
        status="SUCCESS",
        error_message=None,
        execution_time_ms=17,
    )

    assert session.commits == 1
    assert len(session.added) == 1
    assert isinstance(session.added[0], NodeAuditLog)
    assert session.added[0].input_summary["decision"] == "DECLINE"
    assert session.added[0].output_summary["application_id"] == "APP-900"
