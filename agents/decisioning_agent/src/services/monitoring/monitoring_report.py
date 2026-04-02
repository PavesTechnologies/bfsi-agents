"""Monitoring snapshot builder for underwriting telemetry batches."""

from typing import Any, Dict, Iterable

from src.services.monitoring.alerts import evaluate_release_alerts
from src.services.validation.release_report import build_release_report


def build_monitoring_snapshot(
    *,
    baseline_records: Iterable[Dict[str, Any]],
    current_records: Iterable[Dict[str, Any]],
    segment_key: str,
    thresholds: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """Build a report plus alerts for a monitoring cycle."""
    report = build_release_report(
        baseline_records=baseline_records,
        current_records=current_records,
        segment_key=segment_key,
    )
    alerts = evaluate_release_alerts(report, thresholds=thresholds)

    return {
        "segment_key": segment_key,
        "report": report,
        "alerts": alerts,
        "alert_count": len(alerts),
        "high_severity_alert_count": len(
            [alert for alert in alerts if alert.get("severity") == "HIGH"]
        ),
    }
