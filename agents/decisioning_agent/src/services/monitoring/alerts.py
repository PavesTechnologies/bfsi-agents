"""Threshold-based alerts for underwriting monitoring."""

from typing import Any, Dict, List


DEFAULT_ALERT_THRESHOLDS = {
    "approval_rate_change_abs": 0.1,
    "decision_drift_psi": 0.25,
    "risk_tier_drift_psi": 0.25,
    "disparate_impact_ratio_min": 0.8,
    "reason_rate_concentration": 0.7,
}


def evaluate_release_alerts(
    report: Dict[str, Any],
    *,
    thresholds: Dict[str, float] | None = None,
) -> List[Dict[str, Any]]:
    """Evaluate release metrics against alert thresholds."""
    thresholds = {**DEFAULT_ALERT_THRESHOLDS, **(thresholds or {})}
    alerts: List[Dict[str, Any]] = []

    approval_rate_change = abs(report.get("approval_rate_change", 0.0))
    if approval_rate_change >= thresholds["approval_rate_change_abs"]:
        alerts.append(
            {
                "alert_type": "APPROVAL_RATE_SHIFT",
                "severity": "HIGH",
                "metric": "approval_rate_change",
                "value": approval_rate_change,
                "threshold": thresholds["approval_rate_change_abs"],
            }
        )

    for metric_name, threshold_key in (
        ("decision_drift", "decision_drift_psi"),
        ("risk_tier_drift", "risk_tier_drift_psi"),
    ):
        psi = (report.get(metric_name) or {}).get("psi", 0.0)
        if psi >= thresholds[threshold_key]:
            alerts.append(
                {
                    "alert_type": metric_name.upper(),
                    "severity": "HIGH",
                    "metric": f"{metric_name}.psi",
                    "value": psi,
                    "threshold": thresholds[threshold_key],
                }
            )

    current_disparate_impact = report.get("current_disparate_impact", {}).get("segments", {})
    for segment, values in current_disparate_impact.items():
        ratio = values.get("disparate_impact_ratio", 1.0)
        if ratio < thresholds["disparate_impact_ratio_min"]:
            alerts.append(
                {
                    "alert_type": "DISPARATE_IMPACT_BREACH",
                    "severity": "HIGH",
                    "segment": segment,
                    "metric": "disparate_impact_ratio",
                    "value": ratio,
                    "threshold": thresholds["disparate_impact_ratio_min"],
                }
            )

    current_reason_distribution = report.get("current_reason_distribution", {}).get("segments", {})
    for segment, values in current_reason_distribution.items():
        for reason_key, reason_rate in values.get("reason_rates", {}).items():
            if reason_rate >= thresholds["reason_rate_concentration"]:
                alerts.append(
                    {
                        "alert_type": "REASON_CODE_CONCENTRATION",
                        "severity": "MEDIUM",
                        "segment": segment,
                        "reason_key": reason_key,
                        "metric": "reason_rate",
                        "value": reason_rate,
                        "threshold": thresholds["reason_rate_concentration"],
                    }
                )

    return alerts
