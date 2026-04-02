import os
from pathlib import Path

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")

from src.core.versioning import get_runtime_versions
from src.domain.audit.narrative_builder import build_audit_narrative
from src.domain.decisioning.decision_engine import make_underwriting_decision
from src.domain.underwriting_models import UnderwritingResponse
from src.services.validation.release_evidence import build_release_evidence_bundle


DOCS_ROOT = Path(__file__).resolve().parents[1] / "docs"


def test_governance_docs_exist_for_validation_pack():
    required_docs = [
        DOCS_ROOT / "model_inventory.md",
        DOCS_ROOT / "control_matrix.md",
        DOCS_ROOT / "validation_plan.md",
    ]

    for doc_path in required_docs:
        assert doc_path.exists()
        assert doc_path.read_text(encoding="utf-8").strip()


def test_runtime_versions_expose_model_and_prompt_metadata():
    versions = get_runtime_versions()

    assert "model_version" in versions
    assert "prompt_version" in versions
    assert versions["prompt_version"] == "deterministic-underwriting-v1"


def test_validation_pack_proves_deterministic_decision_replay():
    kwargs = {
        "aggregated_risk_tier": "B",
        "credit_score_data": {"base_limit_band": 40000},
        "public_record_data": {
            "public_record_adjustment_factor": 1.0,
            "hard_decline_flag": False,
        },
        "utilization_data": {"utilization_adjustment_factor": 1.0, "utilization_risk": "GOOD"},
        "inquiry_data": {"inquiry_penalty_factor": 1.0},
        "income_data": {"affordability_flag": True, "estimated_dti": 0.31, "income_missing_flag": False},
        "behavior_data": {"chargeoff_history": False},
        "exposure_data": {"exposure_risk": "LOW"},
        "user_request": {"amount": 12000, "tenure": 24},
    }

    first = make_underwriting_decision(**kwargs)
    second = make_underwriting_decision(**kwargs)

    assert first.model_dump() == second.model_dump()
    assert first.decision == "APPROVE"


def test_validation_pack_proves_decline_traceability():
    state = {
        "application_id": "APP-900",
        "policy_metadata": {"policy_version": "v2.0"},
        "version_metadata": {
            "model_version": "openai/gpt-oss-120b",
            "prompt_version": "deterministic-underwriting-v1",
        },
        "aggregated_risk_tier": "F",
        "aggregated_risk_score": 9.5,
        "user_request": {"amount": 25000, "tenure": 36},
        "income_data": {"estimated_dti": 0.58, "affordability_flag": False},
        "utilization_data": {"utilization_ratio": 0.88},
        "exposure_data": {"monthly_obligation_estimate": 2600},
        "credit_score_data": {"score": 610},
        "final_decision": {"approved_amount": 0},
        "decision_result": {"decision": "DECLINE"},
        "parallel_tasks_completed": ["credit_score_engine", "income_engine", "decision_engine"],
    }
    response_payload = {
        "application_id": "APP-900",
        "policy_version": "v2.0",
        "decision": "DECLINE",
        "risk_tier": "F",
        "risk_score": 9.5,
        "primary_reason_key": "BANKRUPTCY_RECENT",
        "secondary_reason_key": "DTI_HIGH",
        "audit_summary": {
            "policy_version": "v2.0",
            "model_version": "openai/gpt-oss-120b",
            "prompt_version": "deterministic-underwriting-v1",
            "decision": "DECLINE",
            "risk_tier": "F",
            "risk_score": 9.5,
            "triggered_reason_keys": ["BANKRUPTCY_RECENT", "DTI_HIGH"],
        },
        "adverse_action_reasons": [
            {"reason_key": "BANKRUPTCY_RECENT", "reason_code": "PR01", "official_text": "Recent bankruptcy on file"},
            {"reason_key": "DTI_HIGH", "reason_code": "01", "official_text": "Debt-to-income ratio too high"},
        ],
        "adverse_action_notice": "Recent bankruptcy on file; Debt-to-income ratio too high",
        "reasoning_summary": "Deterministic decline reasons selected from triggered policy conditions.",
        "key_factors": ["Hard decline public-record trigger", "Debt-to-income ratio above policy threshold"],
        "reasoning_steps": ["Aggregated risk tier evaluated as F.", "Hard decline conditions were met."],
        "decline_reason": "Recent bankruptcy on file",
    }

    narrative = build_audit_narrative(state, response_payload)
    response = UnderwritingResponse.model_validate(response_payload)

    assert narrative["policy_version"] == "v2.0"
    assert narrative["prompt_version"] == "deterministic-underwriting-v1"
    assert narrative["triggered_reason_keys"] == ["BANKRUPTCY_RECENT", "DTI_HIGH"]
    assert response.primary_reason_key == "BANKRUPTCY_RECENT"
    assert response.secondary_reason_key == "DTI_HIGH"
    assert response.audit_summary is not None


def test_validation_pack_can_build_release_evidence_bundle():
    bundle = build_release_evidence_bundle(
        validation_summary={"suite": "validation_pack", "tests_passed": 4},
        monitoring_summary={"alert_count": 0},
        sample_outputs={"approve": {"decision": "APPROVE"}},
    )

    assert bundle["validation_summary"]["tests_passed"] == 4
    assert bundle["governance_docs"]["model_inventory"].endswith("model_inventory.md")
