"""Runtime feature flags for AI-assisted controls."""

import os


def _flag(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def get_feature_flags() -> dict:
    return {
        "ENABLE_LLM_EXPLANATIONS": _flag("ENABLE_LLM_EXPLANATIONS", True),
        "ENABLE_POLICY_RETRIEVAL": _flag("ENABLE_POLICY_RETRIEVAL", True),
        "ENABLE_EXPLANATION_CRITIC": _flag("ENABLE_EXPLANATION_CRITIC", True),
        "ENABLE_MONITORING_ALERTS": _flag("ENABLE_MONITORING_ALERTS", True),
        "FORCE_DETERMINISTIC_EXPLANATIONS_ONLY": _flag(
            "FORCE_DETERMINISTIC_EXPLANATIONS_ONLY",
            False,
        ),
    }
