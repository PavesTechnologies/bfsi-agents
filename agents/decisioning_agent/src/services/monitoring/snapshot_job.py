"""Automated monitoring snapshot job."""

from datetime import datetime, timedelta, timezone

from src.core.feature_flags import get_feature_flags
from src.services.monitoring.alert_dispatcher import dispatch_alerts
from src.services.monitoring.monitoring_report import build_monitoring_snapshot


async def run_monitoring_snapshot_job(
    *,
    underwriting_repository,
    snapshot_repository,
    segment_key: str,
    evaluation_attributes: dict | None = None,
    baseline_days: int = 30,
    current_days: int = 7,
) -> dict:
    now = datetime.now(timezone.utc)
    current_from = now - timedelta(days=current_days)
    baseline_from = now - timedelta(days=baseline_days + current_days)
    baseline_to = current_from

    baseline_records = await underwriting_repository.get_monitoring_payloads(
        date_from=baseline_from,
        date_to=baseline_to,
        evaluation_attributes=evaluation_attributes,
    )
    current_records = await underwriting_repository.get_monitoring_payloads(
        date_from=current_from,
        date_to=now,
        evaluation_attributes=evaluation_attributes,
    )

    snapshot = build_monitoring_snapshot(
        baseline_records=baseline_records,
        current_records=current_records,
        segment_key=segment_key,
    )
    saved = await snapshot_repository.create_snapshot(
        segment_key=segment_key,
        generated_by="snapshot_job",
        thresholds=snapshot["report"].get("thresholds", {}),
        report=snapshot["report"],
        alerts=snapshot["alerts"],
        baseline_records=baseline_records,
        current_records=current_records,
    )

    if get_feature_flags()["ENABLE_MONITORING_ALERTS"]:
        dispatch_alerts(snapshot["alerts"])

    return {
        "run_id": str(saved.id),
        "alert_count": snapshot["alert_count"],
        "high_severity_alert_count": snapshot["high_severity_alert_count"],
        "segment_key": segment_key,
    }
