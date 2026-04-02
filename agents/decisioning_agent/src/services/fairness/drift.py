"""Drift detection helpers for underwriting monitoring."""

import math
from collections import Counter
from typing import Any, Dict, Iterable


def compute_population_stability_index(
    baseline_values: Iterable[Any],
    current_values: Iterable[Any],
) -> Dict[str, Any]:
    """Compute PSI for categorical or bucketed values."""
    baseline_counts = Counter(str(value) for value in baseline_values)
    current_counts = Counter(str(value) for value in current_values)
    all_keys = sorted(set(baseline_counts) | set(current_counts))

    baseline_total = sum(baseline_counts.values())
    current_total = sum(current_counts.values())
    epsilon = 1e-6
    psi = 0.0
    buckets = {}

    for key in all_keys:
        baseline_share = baseline_counts[key] / baseline_total if baseline_total else 0.0
        current_share = current_counts[key] / current_total if current_total else 0.0
        adjusted_baseline = max(baseline_share, epsilon)
        adjusted_current = max(current_share, epsilon)
        contribution = (adjusted_current - adjusted_baseline) * math.log(
            adjusted_current / adjusted_baseline
        )
        psi += contribution
        buckets[key] = {
            "baseline_share": baseline_share,
            "current_share": current_share,
            "psi_contribution": contribution,
        }

    if psi < 0.1:
        severity = "LOW"
    elif psi < 0.25:
        severity = "MODERATE"
    else:
        severity = "HIGH"

    return {
        "psi": psi,
        "severity": severity,
        "buckets": buckets,
    }
