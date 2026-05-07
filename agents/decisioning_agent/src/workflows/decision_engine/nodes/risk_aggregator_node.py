"""
Underwriting Risk Aggregation Engine
Policy-Driven, Auditable Decision Core

Deterministic aggregation of all parallel risk signals into
a single risk score and tier. No LLM needed here.
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node


# -------------------------------------------------------
# Risk Tier Mapping
# -------------------------------------------------------
TIER_MAPPING = [
    (80, "A"),   # 80-100 → Tier A (Prime)
    (65, "B"),   # 65-79  → Tier B (Near-Prime)
    (50, "C"),   # 50-64  → Tier C (Fair)
    (35, "D"),   # 35-49  → Tier D (Subprime)
    (0,  "F"),   # 0-34   → Tier F (Decline)
]


def _score_to_tier(score: float) -> str:
    for threshold, tier in TIER_MAPPING:
        if score >= threshold:
            return tier
    return "F"


# -------------------------------------------------------
# Weight Configuration
# -------------------------------------------------------
WEIGHTS = {
    "credit_score":  0.25,
    "public_record": 0.15,
    "utilization":   0.15,
    "exposure":      0.10,
    "behavior":      0.15,
    "inquiry":       0.05,
    "income":        0.15,
}


def _normalize_risk_flag(flag: str) -> float:
    """Convert a text risk flag to a 0-100 sub-score."""
    mapping = {
        # Credit Score / General flags
        "LOW": 90, "MODERATE": 60, "HIGH": 30,
        # Utilization flags
        "EXCELLENT": 95, "GOOD": 75, "CRITICAL": 10,
        # Exposure flags
        "EXTREME": 5,
        # Behavior flags
        "FAIR": 65, "POOR": 30, "UNACCEPTABLE": 5,
        # Severity flags (public record)
        "NONE": 100, "SEVERE": 10,
    }
    return mapping.get(flag.upper(), 50)


@track_node("underwriting_risk_aggregator")
@audit_node(agent_name="decisioning_agent")
def risk_aggregator_node(state: LoanApplicationState) -> LoanApplicationState:

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
        active_w = {k: v for k, v in WEIGHTS.items() if k in active}
        total_w = sum(active_w.values()) or 1.0
        effective_weights = {k: v / total_w for k, v in active_w.items()}
    else:
        effective_weights = WEIGHTS

    # ==================================================
    # 3️⃣ Compute Sub-Scores (0-100 each) for active analyzers only
    # ==================================================
    sub_scores = {}

    if "credit_score" in effective_weights:
        raw_score = credit.get("score", 0) or 0
        sub_scores["credit_score"] = max(0, min(100, (raw_score - 300) / 5.5))

    if "public_record" in effective_weights:
        sub_scores["public_record"] = _normalize_risk_flag(
            public.get("public_record_severity", "NONE")
        )

    if "utilization" in effective_weights:
        sub_scores["utilization"] = _normalize_risk_flag(
            util.get("utilization_risk", "GOOD")
        )

    if "exposure" in effective_weights:
        sub_scores["exposure"] = _normalize_risk_flag(
            exposure.get("exposure_risk", "LOW")
        )

    if "behavior" in effective_weights:
        sub_scores["behavior"] = behavior.get("behavior_score", 50) or 50

    if "inquiry" in effective_weights:
        sub_scores["inquiry"] = _normalize_risk_flag(
            inquiry.get("velocity_risk", "LOW")
        )

    if "income" in effective_weights:
        sub_scores["income"] = _normalize_risk_flag(
            income.get("income_risk", "MODERATE")
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
    aggregated_risk_tier = _score_to_tier(aggregated_risk_score)

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