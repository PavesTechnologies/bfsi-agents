"""Citation-aware explanation generation with deterministic fallback."""

from src.core.feature_flags import get_feature_flags
from src.services.llm_executor import execute_llm
from src.services.operations.kill_switch import get_kill_switch_state
from src.services.policy_retrieval.retriever import retrieve_policy_evidence
from src.services.prompts.constitutional_underwriting_prompt import (
    CONSTITUTIONAL_UNDERWRITING_PROMPT,
)
from src.services.validation.explanation_critic import critique_explanation


def _deterministic_explanation(
    *,
    decision: str,
    reason_keys: list[str],
    key_factors: list[str],
    evidence: list[dict],
) -> dict:
    if decision == "APPROVE":
        text = "Approved under deterministic policy thresholds."
    elif decision == "COUNTER_OFFER":
        text = "A counter offer was generated because the requested amount exceeded deterministic lending capacity."
    elif decision == "REFER_TO_HUMAN":
        text = "Application was routed to human review based on deterministic policy gates."
    else:
        reason_text = ", ".join(reason_keys) if reason_keys else "deterministic decline conditions"
        factor_text = "; ".join(key_factors[:2]) if key_factors else "policy threshold triggers"
        text = f"Declined due to {reason_text}. Key supporting factors: {factor_text}."

    return {
        "explanation_text": text,
        "cited_sections": [item.get("section_id") for item in evidence[:2] if item.get("section_id")],
        "citation_confidence": "HIGH" if evidence else "LOW",
        "generation_mode": "deterministic_fallback",
    }


def build_cited_explanation(
    *,
    deterministic_outcome: dict,
) -> dict:
    reason_keys = [
        key
        for key in [
            deterministic_outcome.get("primary_reason_key"),
            deterministic_outcome.get("secondary_reason_key"),
        ]
        if key
    ]
    key_factors = deterministic_outcome.get("key_factors", []) or []
    flags = get_feature_flags()
    kill_switch = get_kill_switch_state()
    evidence = (
        retrieve_policy_evidence(reason_keys=reason_keys, key_factors=key_factors)
        if flags["ENABLE_POLICY_RETRIEVAL"] and kill_switch["policy_retrieval_enabled"]
        else []
    )

    fallback = _deterministic_explanation(
        decision=deterministic_outcome.get("decision", "UNKNOWN"),
        reason_keys=reason_keys,
        key_factors=key_factors,
        evidence=evidence,
    )

    if not flags["ENABLE_LLM_EXPLANATIONS"] or kill_switch["deterministic_only"] or not kill_switch["llm_explanations_enabled"]:
        result = fallback
    else:
        llm_result = execute_llm(
            prompt_template=CONSTITUTIONAL_UNDERWRITING_PROMPT,
            inputs={
                "deterministic_outcome": deterministic_outcome,
                "policy_evidence": evidence,
            },
            temperature=0.0,
            max_retries=0,
            fallback_result=fallback,
        )
        if isinstance(llm_result, dict):
            result = {
                "explanation_text": llm_result.get("explanation_text") or fallback["explanation_text"],
                "cited_sections": llm_result.get("cited_sections") or fallback["cited_sections"],
                "citation_confidence": llm_result.get("citation_confidence") or fallback["citation_confidence"],
                "generation_mode": "llm",
            }
        else:
            result = fallback

    critic = critique_explanation(
        explanation_text=result["explanation_text"],
        reason_keys=reason_keys,
        cited_sections=result.get("cited_sections", []),
        policy_evidence=evidence,
    )
    if flags["ENABLE_EXPLANATION_CRITIC"] and kill_switch["critic_enabled"] and not critic["passed"]:
        result = {
            **fallback,
            "critic_failures": critic["failures"],
        }
    else:
        result["critic_failures"] = []

    result["policy_evidence"] = evidence
    return result
