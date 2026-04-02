"""Release evidence bundle generation for governance and model risk review."""

from pathlib import Path

from src.core.feature_flags import get_feature_flags
from src.core.versioning import get_runtime_versions
from src.policy.policy_registry import get_active_policy
from src.policy.versioning import build_policy_version_metadata


def build_release_evidence_bundle(
    *,
    validation_summary: dict,
    monitoring_summary: dict | None = None,
    sample_outputs: dict | None = None,
) -> dict:
    policy = get_active_policy()
    docs_root = Path(__file__).resolve().parents[3] / "docs"

    return {
        "service": "decisioning_agent",
        "runtime_versions": get_runtime_versions(),
        "policy_versions": build_policy_version_metadata(policy),
        "feature_flags": get_feature_flags(),
        "validation_summary": validation_summary,
        "monitoring_summary": monitoring_summary or {},
        "sample_outputs": sample_outputs or {},
        "governance_docs": {
            "model_inventory": str(docs_root / "model_inventory.md"),
            "control_matrix": str(docs_root / "control_matrix.md"),
            "validation_plan": str(docs_root / "validation_plan.md"),
        },
    }
