from src.domain.monitoring_models import (
    MonitoringSnapshotRequest,
    MonitoringSnapshotResponse,
    MonitoringSnapshotSummary,
)
from src.repositories.underwriting_monitoring_snapshot_repository import (
    UnderwritingMonitoringSnapshotRepository,
)
from src.services.monitoring.alerts import DEFAULT_ALERT_THRESHOLDS
from src.services.monitoring.monitoring_report import build_monitoring_snapshot


class UnderwritingMonitoringService:
    def __init__(self, db):
        self.snapshot_repo = UnderwritingMonitoringSnapshotRepository(db)

    async def generate_snapshot(
        self,
        request: MonitoringSnapshotRequest,
    ) -> MonitoringSnapshotResponse:
        thresholds = {**DEFAULT_ALERT_THRESHOLDS, **(request.thresholds or {})}
        snapshot = build_monitoring_snapshot(
            baseline_records=request.baseline_records,
            current_records=request.current_records,
            segment_key=request.segment_key,
            thresholds=thresholds,
        )

        saved = await self.snapshot_repo.create_snapshot(
            segment_key=request.segment_key,
            generated_by=request.generated_by,
            thresholds=thresholds,
            report=snapshot["report"],
            alerts=snapshot["alerts"],
            baseline_records=request.baseline_records,
            current_records=request.current_records,
        )

        return MonitoringSnapshotResponse(
            run_id=str(saved.id),
            segment_key=saved.segment_key,
            alert_count=snapshot["alert_count"],
            high_severity_alert_count=snapshot["high_severity_alert_count"],
            report=saved.report,
            alerts=list(saved.alerts),
            thresholds=saved.thresholds,
            generated_by=saved.generated_by,
            created_at=saved.created_at,
        )

    async def get_latest_snapshot(
        self,
        segment_key: str,
    ) -> MonitoringSnapshotSummary:
        latest = await self.snapshot_repo.get_latest_snapshot(segment_key)
        if latest is None:
            return MonitoringSnapshotSummary(segment_key=segment_key, latest_snapshot=None)

        alerts = list(latest.alerts)
        return MonitoringSnapshotSummary(
            segment_key=segment_key,
            latest_snapshot=MonitoringSnapshotResponse(
                run_id=str(latest.id),
                segment_key=latest.segment_key,
                alert_count=len(alerts),
                high_severity_alert_count=len(
                    [alert for alert in alerts if alert.get("severity") == "HIGH"]
                ),
                report=latest.report,
                alerts=alerts,
                thresholds=latest.thresholds,
                generated_by=latest.generated_by,
                created_at=latest.created_at,
            ),
        )
