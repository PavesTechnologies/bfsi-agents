"""Helpers for enforcing constrained underwriting decision outputs."""

from src.domain.reason_codes.reason_registry import REGULATORY_REASON_MAPPING, reason_details


def submit_decline_decision(
    *,
    primary_reason_key: str,
    secondary_reason_key: str,
    reasoning_summary: str,
) -> dict:
    reason_keys = [primary_reason_key, secondary_reason_key]
    if len(reason_keys) != 2:
        raise ValueError("Decline decisions must include exactly two principal reason keys.")

    if primary_reason_key == secondary_reason_key:
        raise ValueError("Primary and secondary reason keys must be distinct.")

    for reason_key in reason_keys:
        if reason_key not in REGULATORY_REASON_MAPPING:
            raise ValueError(f"Unknown regulatory reason key: {reason_key}")

    reasons = [reason_details(reason_key) for reason_key in reason_keys]
    notice = "; ".join(reason["official_text"] for reason in reasons)

    return {
        "primary_reason_key": primary_reason_key,
        "secondary_reason_key": secondary_reason_key,
        "adverse_action_reasons": reasons,
        "adverse_action_notice": notice,
        "reasoning_summary": reasoning_summary,
    }
