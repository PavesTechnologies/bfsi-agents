"""Release validation summaries for underwriting changes."""

from typing import Any, Dict, Iterable

from src.services.fairness.disparate_impact import compute_disparate_impact
from src.services.fairness.drift import compute_population_stability_index
from src.services.fairness.reason_code_analysis import summarize_reason_code_distribution


def build_release_report(
    *,
    baseline_records: Iterable[Dict[str, Any]],
    current_records: Iterable[Dict[str, Any]],
    segment_key: str,
) -> Dict[str, Any]:
    baseline_records = list(baseline_records)
    current_records = list(current_records)

    baseline_approval_rate = (
        sum(1 for record in baseline_records if record.get("is_approved")) / len(baseline_records)
        if baseline_records
        else 0.0
    )
    current_approval_rate = (
        sum(1 for record in current_records if record.get("is_approved")) / len(current_records)
        if current_records
        else 0.0
    )

    return {
        "baseline_sample_size": len(baseline_records),
        "current_sample_size": len(current_records),
        "approval_rate_change": current_approval_rate - baseline_approval_rate,
        "baseline_approval_rate": baseline_approval_rate,
        "current_approval_rate": current_approval_rate,
        "decision_drift": compute_population_stability_index(
            [record.get("decision") for record in baseline_records],
            [record.get("decision") for record in current_records],
        ),
        "risk_tier_drift": compute_population_stability_index(
            [record.get("risk_tier") for record in baseline_records],
            [record.get("risk_tier") for record in current_records],
        ),
        "baseline_disparate_impact": compute_disparate_impact(
            baseline_records,
            segment_key=segment_key,
        ),
        "current_disparate_impact": compute_disparate_impact(
            current_records,
            segment_key=segment_key,
        ),
        "baseline_reason_distribution": summarize_reason_code_distribution(
            baseline_records,
            segment_key=segment_key,
        ),
        "current_reason_distribution": summarize_reason_code_distribution(
            current_records,
            segment_key=segment_key,
        ),
    }
