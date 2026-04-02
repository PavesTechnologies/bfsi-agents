"""
Underwriting Risk Aggregation Engine
Policy-driven deterministic aggregation of risk signals.
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.domain.attribution.score_contribution import build_score_contribution
from src.policy.policy_registry import get_active_policy
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


def _score_to_tier(score: float) -> str:
    for item in get_active_policy().risk_tiers:
        if score >= item.threshold:
            return item.tier
    return "F"


def _normalize_risk_flag(flag: str) -> float:
    mapping = {
        "LOW": 90,
        "MODERATE": 60,
        "HIGH": 30,
        "EXCELLENT": 95,
        "GOOD": 75,
        "CRITICAL": 10,
        "EXTREME": 5,
        "FAIR": 65,
        "POOR": 30,
        "UNACCEPTABLE": 5,
        "NONE": 100,
        "SEVERE": 10,
    }
    return mapping.get(str(flag).upper(), 50)


@track_node("underwriting_risk_aggregator")
@audit_node(agent_name="decisioning_agent")
def risk_aggregator_node(state: LoanApplicationState) -> LoanApplicationState:
    policy = get_active_policy()
    weights = {
        "credit_score": policy.risk_weights.credit_score,
        "public_record": policy.risk_weights.public_records,
        "utilization": policy.risk_weights.utilization,
        "exposure": 0.0,
        "behavior": policy.risk_weights.payment_behavior,
        "inquiry": policy.risk_weights.inquiries,
        "income": policy.risk_weights.affordability,
    }

    credit = state.get("credit_score_data") or {}
    public = state.get("public_record_data") or {}
    util = state.get("utilization_data") or {}
    exposure = state.get("exposure_data") or {}
    behavior = state.get("behavior_data") or {}
    inquiry = state.get("inquiry_data") or {}
    income = state.get("income_data") or {}

    sub_scores = {
        "credit_score": max(0, min(100, ((credit.get("score", 0) or 0) - 300) / 5.5)),
        "public_record": _normalize_risk_flag(public.get("public_record_severity", "NONE")),
        "utilization": _normalize_risk_flag(util.get("utilization_risk", "GOOD")),
        "exposure": _normalize_risk_flag(exposure.get("exposure_risk", "LOW")),
        "behavior": behavior.get("behavior_score", 50) or 50,
        "inquiry": _normalize_risk_flag(inquiry.get("velocity_risk", "LOW")),
        "income": _normalize_risk_flag(income.get("income_risk", "MODERATE")),
    }

    aggregated_risk_score = round(
        sum(sub_scores[key] * weights[key] for key in weights),
        2,
    )

    hard_decline = public.get("hard_decline_flag", False)
    if hard_decline:
        aggregated_risk_score = 0.0

    aggregated_risk_tier = _score_to_tier(aggregated_risk_score)

    reasoning_trace = {
        "sub_scores": sub_scores,
        "weights": weights,
        "score_contribution": build_score_contribution(sub_scores, weights),
        "hard_decline_override": hard_decline,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return {
        "aggregated_risk_score": aggregated_risk_score,
        "aggregated_risk_tier": aggregated_risk_tier,
        "reasoning_trace": reasoning_trace,
    }
