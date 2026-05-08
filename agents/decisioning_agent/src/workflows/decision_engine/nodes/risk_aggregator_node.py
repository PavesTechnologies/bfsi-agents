"""
Underwriting Risk Aggregation Engine
Policy-Driven, Auditable Decision Core

Deterministic aggregation of all parallel risk signals into a single risk
score and tier. No LLM needed here. Tier thresholds, per-analyzer weights,
and risk-flag-to-score mappings are read from `rules_per_node['decision']`
(loaded by `rules_loader_node` from the bank-admin DB).
"""

from datetime import datetime
from typing import Any

from src.core.telemetry import track_node
from src.services.rules_db import MissingRuleError
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node


_DEFAULT_RISK_FLAG_FALLBACK = 50  # only used when LLM emits an unmapped flag


def _decision_rules(state: LoanApplicationState) -> dict[str, Any]:
    rules = (state.get("rules_per_node") or {}).get("decision")
    if not rules:
        raise MissingRuleError(rule_key="<decision-bucket>", category="decision")
    return rules


def _score_to_tier(score: float, tier_thresholds: list[dict[str, Any]]) -> str:
    """`tier_thresholds` is a list of {"tier": "A", "min": 80} sorted high→low.
    Defensive: re-sort by `min` desc so DB row order can't change semantics."""
    ordered = sorted(tier_thresholds, key=lambda r: float(r["min"]), reverse=True)
    for row in ordered:
        if score >= float(row["min"]):
            return str(row["tier"])
    return str(ordered[-1]["tier"]) if ordered else "F"


def _normalize_risk_flag(flag: str, mapping: dict[str, int]) -> float:
    """Convert a text risk flag to a 0-100 sub-score using the DB-loaded map."""
    return float(mapping.get(flag.upper(), _DEFAULT_RISK_FLAG_FALLBACK))


@track_node("underwriting_risk_aggregator")
@audit_node(agent_name="decisioning_agent")
def risk_aggregator_node(state: LoanApplicationState) -> LoanApplicationState:
    decision_rules = _decision_rules(state)
    weights: dict[str, float] = decision_rules["risk_weights"]
    tier_thresholds: list[dict[str, Any]] = decision_rules["tier_thresholds"]
    risk_flag_score_map: dict[str, int] = decision_rules["risk_flag_score_map"]

    # ==================================================
    # 1️⃣ Extract Signals
    # ==================================================
    credit   = state.get("credit_score_data") or {}
    public   = state.get("public_record_data") or {}
    util     = state.get("utilization_data") or {}
    exposure = state.get("exposure_data") or {}
    behavior = state.get("behavior_data") or {}
    inquiry  = state.get("inquiry_data") or {}
    income   = state.get("income_data") or {}

    # ==================================================
    # 2️⃣ Determine effective weights (redistribute for inactive analyzers)
    # ==================================================
    active = state.get("active_analyzers")
    if active is not None:
        active_w = {k: v for k, v in weights.items() if k in active}
        total_w = sum(active_w.values()) or 1.0
        effective_weights = {k: v / total_w for k, v in active_w.items()}
    else:
        effective_weights = weights

    # ==================================================
    # 3️⃣ Compute Sub-Scores (0-100 each) for active analyzers only
    # ==================================================
    sub_scores = {}

    if "credit_score" in effective_weights:
        raw_score = credit.get("score", 0) or 0
        sub_scores["credit_score"] = max(0, min(100, (raw_score - 300) / 5.5))

    if "public_record" in effective_weights:
        sub_scores["public_record"] = _normalize_risk_flag(
            public.get("public_record_severity", "NONE"), risk_flag_score_map
        )

    if "utilization" in effective_weights:
        sub_scores["utilization"] = _normalize_risk_flag(
            util.get("utilization_risk", "GOOD"), risk_flag_score_map
        )

    if "exposure" in effective_weights:
        sub_scores["exposure"] = _normalize_risk_flag(
            exposure.get("exposure_risk", "LOW"), risk_flag_score_map
        )

    if "behavior" in effective_weights:
        sub_scores["behavior"] = behavior.get("behavior_score", 50) or 50

    if "inquiry" in effective_weights:
        sub_scores["inquiry"] = _normalize_risk_flag(
            inquiry.get("velocity_risk", "LOW"), risk_flag_score_map
        )

    if "income" in effective_weights:
        sub_scores["income"] = _normalize_risk_flag(
            income.get("income_risk", "MODERATE"), risk_flag_score_map
        )

    # ==================================================
    # 4️⃣ Weighted Aggregation
    # ==================================================
    aggregated_risk_score = sum(
        sub_scores[key] * effective_weights[key] for key in effective_weights
    )

    # Round to 2 decimal places
    aggregated_risk_score = round(aggregated_risk_score, 2)

    # ==================================================
    # 5️⃣ Check Hard-Decline Override
    # ==================================================
    hard_decline = public.get("hard_decline_flag", False)
    if hard_decline:
        aggregated_risk_score = 0.0

    # ==================================================
    # 6️⃣ Determine Risk Tier
    # ==================================================
    aggregated_risk_tier = _score_to_tier(aggregated_risk_score, tier_thresholds)

    # ==================================================
    # 7️⃣ Build Reasoning Trace
    # ==================================================
    reasoning_trace = {
        "sub_scores": sub_scores,
        "weights": effective_weights,
        "active_analyzers": active,
        "hard_decline_override": hard_decline,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return {
        "aggregated_risk_score": aggregated_risk_score,
        "aggregated_risk_tier": aggregated_risk_tier,
        "reasoning_trace": reasoning_trace,
    }
