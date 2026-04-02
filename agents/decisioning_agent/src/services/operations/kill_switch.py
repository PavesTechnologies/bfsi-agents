"""Operational kill switch for AI-assisted components."""

from src.core.feature_flags import get_feature_flags


def get_kill_switch_state() -> dict:
    flags = get_feature_flags()
    return {
        "llm_explanations_enabled": flags["ENABLE_LLM_EXPLANATIONS"]
        and not flags["FORCE_DETERMINISTIC_EXPLANATIONS_ONLY"],
        "policy_retrieval_enabled": flags["ENABLE_POLICY_RETRIEVAL"],
        "critic_enabled": flags["ENABLE_EXPLANATION_CRITIC"],
        "deterministic_only": flags["FORCE_DETERMINISTIC_EXPLANATIONS_ONLY"],
    }
