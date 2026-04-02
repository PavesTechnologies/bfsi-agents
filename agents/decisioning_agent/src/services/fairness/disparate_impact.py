"""Fairness analytics for decision outcome disparities."""

from collections import defaultdict
from typing import Any, Dict, Iterable


def compute_disparate_impact(
    records: Iterable[Dict[str, Any]],
    *,
    segment_key: str,
    positive_key: str = "is_approved",
) -> Dict[str, Any]:
    """Compute approval-rate disparity across evaluation segments."""
    grouped: dict[str, list[bool]] = defaultdict(list)

    for record in records:
        attributes = record.get("evaluation_attributes", {})
        segment = attributes.get(segment_key)
        if segment is None:
            continue
        grouped[str(segment)].append(bool(record.get(positive_key, False)))

    segments = {}
    max_rate = 0.0
    reference_segment = None

    for segment, outcomes in grouped.items():
        sample_size = len(outcomes)
        positive_rate = sum(outcomes) / sample_size if sample_size else 0.0
        segments[segment] = {
            "sample_size": sample_size,
            "positive_rate": positive_rate,
        }
        if positive_rate > max_rate:
            max_rate = positive_rate
            reference_segment = segment

    for segment, values in segments.items():
        values["disparate_impact_ratio"] = (
            values["positive_rate"] / max_rate if max_rate else 0.0
        )
        values["passes_four_fifths_rule"] = values["disparate_impact_ratio"] >= 0.8

    return {
        "segment_key": segment_key,
        "reference_segment": reference_segment,
        "reference_positive_rate": max_rate,
        "segments": segments,
    }
