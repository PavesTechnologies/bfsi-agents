"""Deterministic adverse-action reason selection."""

from src.domain.decisioning.decision_submission import submit_decline_decision
from src.domain.reason_codes.disclosure_templates import DISCLOSURE_TEMPLATES
from src.domain.reason_codes.reason_registry import (
    REGULATORY_REASON_MAPPING,
)
from src.domain.reason_codes.reason_types import ReasonSelectionContext
from src.domain.reason_codes.trigger_engine import evaluate_reason_triggers


def select_decline_reasons(
    *,
    aggregated_risk_tier: str,
    public_record_data: dict,
    income_data: dict,
    behavior_data: dict,
    utilization_data: dict,
    exposure_data: dict,
    inquiry_data: dict,
    credit_score_data: dict | None = None,
    product_code: str = "UNSECURED_PERSONAL_LOAN",
) -> dict:
    trigger_results = evaluate_reason_triggers(
        ReasonSelectionContext(
            product_code=product_code,
            aggregated_risk_tier=aggregated_risk_tier,
            public_record_data=public_record_data,
            income_data=income_data,
            behavior_data=behavior_data,
            utilization_data=utilization_data,
            exposure_data=exposure_data,
            inquiry_data=inquiry_data,
            credit_score_data=credit_score_data or {},
        )
    )
    candidates = [candidate.reason_key for candidate in trigger_results]

    if not candidates:
        candidates = ["RISK_TIER_F"]
        trigger_results = []

    selected = candidates[:2]
    if len(selected) == 1:
        selected.append("RISK_TIER_F" if selected[0] != "RISK_TIER_F" else "EXPOSURE_HIGH")

    submission = submit_decline_decision(
        primary_reason_key=selected[0],
        secondary_reason_key=selected[1],
        reasoning_summary="Deterministic decline reasons selected from triggered policy conditions.",
    )
    submission["candidate_reason_codes"] = [candidate.model_dump() for candidate in trigger_results]
    submission["selected_reason_codes"] = [
        {
            "reason_key": reason_key,
            "reason_code": REGULATORY_REASON_MAPPING[reason_key]["reason_code"],
            "reviewer_text": DISCLOSURE_TEMPLATES[reason_key]["reviewer_text"],
            "internal_text": DISCLOSURE_TEMPLATES[reason_key]["internal_text"],
        }
        for reason_key in selected
    ]
    return submission
