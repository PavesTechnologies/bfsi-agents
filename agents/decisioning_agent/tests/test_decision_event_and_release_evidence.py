import os
from types import SimpleNamespace
import json

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("SERVICE_NAME", "decisioning_agent")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://test:test@localhost:5432/testdb")

import pytest

from src.models.underwriting_decision_event import UnderwritingDecisionEvent
from src.repositories.underwriting_repository import UnderwritingRepository
from src.services.validation.release_artifact_writer import write_release_evidence_bundle
from src.services.validation.release_evidence import build_release_evidence_bundle


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, value):
        if getattr(value, "id", None) is None:
            setattr(value, "id", f"id-{len(self.added)+1}")
        self.added.append(value)

    async def commit(self):
        self.commits += 1


@pytest.mark.anyio
async def test_underwriting_repository_writes_decision_event():
    session = FakeSession()
    repo = UnderwritingRepository(session)

    await repo.save_decision(
        application_id="APP-500",
        decision="DECLINE",
        final_decision={
            "decision": "DECLINE",
            "decline_reason": "Debt-to-income ratio too high",
            "primary_reason_key": "DTI_HIGH",
            "secondary_reason_key": "EXPOSURE_HIGH",
            "adverse_action_reasons": [],
            "reasoning_steps": ["step 1"],
            "candidate_reason_codes": [{"reason_key": "DTI_HIGH"}],
            "selected_reason_codes": [{"reason_key": "DTI_HIGH"}, {"reason_key": "EXPOSURE_HIGH"}],
            "policy_citations": [{"section_id": "4.2"}],
            "retrieval_evidence": [{"section_id": "4.2", "content": "Applicants with debt-to-income ratios above 45%"}],
            "feature_attribution_summary": {"rule_attribution": [{"rule": "dti_threshold"}]},
            "explanation_generation_mode": "deterministic_fallback",
            "critic_failures": [],
        },
        aggregated_risk_score=12.5,
        aggregated_risk_tier="F",
        policy_version="v2.0",
        model_version="openai/gpt-oss-120b",
        prompt_version="deterministic-underwriting-v1",
        audit_narrative={"application_id": "APP-500", "decision": "DECLINE"},
    )

    assert session.commits == 2
    assert any(isinstance(item, UnderwritingDecisionEvent) for item in session.added)
    decision_record = next(item for item in session.added if not isinstance(item, UnderwritingDecisionEvent))
    assert decision_record.policy_citations[0]["section_id"] == "4.2"
    assert decision_record.explanation_generation_mode == "deterministic_fallback"


def test_release_evidence_bundle_contains_versions_flags_and_docs():
    bundle = build_release_evidence_bundle(
        validation_summary={"tests_passed": 42},
        monitoring_summary={"alert_count": 0},
        sample_outputs={"decline": {"decision": "DECLINE"}},
    )

    assert bundle["runtime_versions"]["prompt_version"] == "deterministic-underwriting-v1"
    assert bundle["policy_versions"]["policy_version"] == "v2.0"
    assert "feature_flags" in bundle
    assert "governance_docs" in bundle


def test_release_artifact_writer_exports_json_bundle(tmp_path):
    output_path = write_release_evidence_bundle(
        output_dir=str(tmp_path),
        validation_summary={"tests_passed": 10},
        monitoring_summary={"alert_count": 1},
        sample_outputs={"decline": {"decision": "DECLINE"}},
    )

    payload = json.loads((tmp_path / os.path.basename(output_path)).read_text(encoding="utf-8"))
    assert payload["validation_summary"]["tests_passed"] == 10
    assert payload["monitoring_summary"]["alert_count"] == 1
