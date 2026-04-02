"""Reason-code distribution analysis across evaluation segments."""

from collections import defaultdict
from typing import Any, Dict, Iterable


def summarize_reason_code_distribution(
    records: Iterable[Dict[str, Any]],
    *,
    segment_key: str,
) -> Dict[str, Any]:
    grouped_reason_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    grouped_totals: dict[str, int] = defaultdict(int)

    for record in records:
        attributes = record.get("evaluation_attributes", {})
        segment = attributes.get(segment_key)
        if segment is None:
            continue

        reason_keys = record.get("triggered_reason_keys", [])
        grouped_totals[str(segment)] += 1
        for reason_key in reason_keys:
            grouped_reason_counts[str(segment)][reason_key] += 1

    segments = {}
    for segment, counts in grouped_reason_counts.items():
        total = grouped_totals[segment]
        segments[segment] = {
            "sample_size": total,
            "reason_counts": dict(counts),
            "reason_rates": {
                reason_key: count / total if total else 0.0
                for reason_key, count in counts.items()
            },
        }

    return {
        "segment_key": segment_key,
        "segments": segments,
    }
