"""
Rules loader — fetches bank_rules from the bank-admin DB and stages them on
state for downstream analyzer / aggregator / decision nodes.

Replaces the per-node bank_policies RAG retrieval. Sits between the (RBI-only)
`rag_retrieval_node` and the parallel analyzer fan-out.

Two outputs land on state:
  * `rules_per_node`       — structured `{node_key: {rule_key: value}}` for
                             deterministic logic (DTI threshold, tier weights,
                             interest rates, etc.)
  * `rag_context_per_node` — same data formatted as prompt-ready text for the
                             {policy_context} slot in analyzer prompts.

Missing required rules raise `MissingRuleError` so the application halts
rather than silently using stale code-defaults.
"""

import logging
from typing import Any

from src.core.telemetry import track_node
from src.services.rules_db import (
    MissingRuleError,
    fetch_rules_for_categories,
    format_rules_for_prompt,
)
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState

logger = logging.getLogger(__name__)


# Workflow-node-key → DB-rule-category-name(s).
# Categories listed for a given node are merged into a single rules dict.
_NODE_TO_CATEGORIES: dict[str, tuple[str, ...]] = {
    "credit_score": ("credit_score",),
    "public_record": ("public_record",),
    "credit_utilization": ("utilization",),
    "debt_exposure": ("exposure",),
    "payment_behavior": ("behavior",),
    "inquiry": ("inquiry",),
    "income_analysis": ("income", "dti"),
    "decision": ("decision",),
}

# Rule keys each node *must* find in the DB. If absent, the run aborts.
# Single-value rules from 001_initial_schema are required only when the node
# actually uses them; band-style configs from 003_decisioning_rules are
# universally required.
_REQUIRED_RULES_PER_NODE: dict[str, tuple[str, ...]] = {
    "credit_score": ("score_bands",),
    "public_record": ("severity_bands", "bankruptcy_hard_decline_years"),
    "credit_utilization": ("utilization_bands",),
    "debt_exposure": ("monthly_obligation_bands", "emi_estimation_pct_of_balance"),
    "payment_behavior": ("delinquency_bands", "chargeoff_dpd_codes", "chargeoff_hard_decline"),
    "inquiry": ("inquiry_velocity_bands",),
    "income_analysis": ("dti_bands", "max_dti_threshold"),
    "decision": ("tier_thresholds", "tier_interest_rates", "risk_weights", "risk_flag_score_map", "origination_fee_pct"),
}


def _all_categories() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for cats in _NODE_TO_CATEGORIES.values():
        for c in cats:
            if c not in seen:
                seen.add(c)
                out.append(c)
    return out


def _merge(category_map: dict[str, dict[str, Any]], cats: tuple[str, ...]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for cat in cats:
        merged.update(category_map.get(cat, {}))
    return merged


def _validate_required(node_key: str, rules: dict[str, Any]) -> None:
    for required_key in _REQUIRED_RULES_PER_NODE.get(node_key, ()):
        if required_key not in rules:
            # Report the *first* category for the node so ops know where to look.
            category = _NODE_TO_CATEGORIES[node_key][0]
            raise MissingRuleError(rule_key=required_key, category=category)


@track_node("rules_loader")
@audit_node(agent_name="decisioning_agent")
async def rules_loader_node(state: LoanApplicationState) -> LoanApplicationState:
    category_map = await fetch_rules_for_categories(_all_categories())

    rules_per_node: dict[str, dict[str, Any]] = {}
    rag_context_per_node: dict[str, str] = dict(state.get("rag_context_per_node") or {})

    for node_key, cats in _NODE_TO_CATEGORIES.items():
        merged = _merge(category_map, cats)
        _validate_required(node_key, merged)
        rules_per_node[node_key] = merged
        rag_context_per_node[node_key] = format_rules_for_prompt(merged)

    populated = sum(1 for v in rag_context_per_node.values() if v)
    logger.info(
        "Rules loader complete: nodes=%d, categories=%d, populated=%d",
        len(rules_per_node), len(category_map), populated,
    )

    return {
        "rules_per_node": rules_per_node,
        "rag_context_per_node": rag_context_per_node,
    }
