"""
Underwriting Risk Aggregation Engine
Policy-Driven, Auditable Decision Core

Deterministic aggregation of all parallel risk signals into
a single risk score and tier. No LLM needed here.
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState


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
    # 2️⃣ Compute Sub-Scores (0-100 each)
    # ==================================================
    sub_scores = {}

    # Credit Score: map 300-850 range to 0-100
    raw_score = credit.get("score", 0) or 0
    sub_scores["credit_score"] = max(0, min(100, (raw_score - 300) / 5.5))

    # Public Record: use severity flag
    sub_scores["public_record"] = _normalize_risk_flag(
        public.get("public_record_severity", "NONE")
    )

    # Utilization: use risk flag
    sub_scores["utilization"] = _normalize_risk_flag(
        util.get("utilization_risk", "GOOD")
    )

    # Exposure: use risk flag
    sub_scores["exposure"] = _normalize_risk_flag(
        exposure.get("exposure_risk", "LOW")
    )

    # Behavior: use behavior_score directly (already 0-100)
    sub_scores["behavior"] = behavior.get("behavior_score", 50) or 50

    # Inquiry: use risk flag
    sub_scores["inquiry"] = _normalize_risk_flag(
        inquiry.get("velocity_risk", "LOW")
    )

    # Income: use risk flag
    sub_scores["income"] = _normalize_risk_flag(
        income.get("income_risk", "MODERATE")
    )

    # ==================================================
    # 3️⃣ Weighted Aggregation
    # ==================================================
    aggregated_risk_score = sum(
        sub_scores[key] * WEIGHTS[key] for key in WEIGHTS
    )

    # Round to 2 decimal places
    aggregated_risk_score = round(aggregated_risk_score, 2)

    # ==================================================
    # 4️⃣ Check Hard-Decline Override
    # ==================================================
    hard_decline = public.get("hard_decline_flag", False)
    if hard_decline:
        aggregated_risk_score = 0.0

    # ==================================================
    # 5️⃣ Determine Risk Tier
    # ==================================================
    aggregated_risk_tier = _score_to_tier(aggregated_risk_score)

    # ==================================================
    # 6️⃣ Build Reasoning Trace
    # ==================================================
    reasoning_trace = {
        "sub_scores": sub_scores,
        "weights": WEIGHTS,
        "hard_decline_override": hard_decline,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return {
        "aggregated_risk_score": aggregated_risk_score,
        "aggregated_risk_tier": aggregated_risk_tier,
        "reasoning_trace": reasoning_trace,
    }