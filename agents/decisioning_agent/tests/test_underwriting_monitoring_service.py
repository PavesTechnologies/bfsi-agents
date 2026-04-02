from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.domain.monitoring_models import MonitoringSnapshotRequest
from src.services.monitoring.alerts import DEFAULT_ALERT_THRESHOLDS
from src.services.underwriting_monitoring_service import UnderwritingMonitoringService


class FakeMonitoringSnapshotRepo:
    def __init__(self):
        self.created = []
        self.latest_by_segment = {}

    async def create_snapshot(self, **kwargs):
        self.created.append(kwargs)
        record = SimpleNamespace(
            id=uuid4(),
            segment_key=kwargs["segment_key"],
            generated_by=kwargs["generated_by"],
            thresholds=kwargs["thresholds"],
            report=kwargs["report"],
            alerts=kwargs["alerts"],
            baseline_records=kwargs["baseline_records"],
            current_records=kwargs["current_records"],
            created_at=datetime.now(timezone.utc),
        )
        self.latest_by_segment[kwargs["segment_key"]] = record
        return record

    async def get_latest_snapshot(self, segment_key):
        return self.latest_by_segment.get(segment_key)


def build_service():
    service = UnderwritingMonitoringService.__new__(UnderwritingMonitoringService)
    service.snapshot_repo = FakeMonitoringSnapshotRepo()
    return service


def build_request():
    return MonitoringSnapshotRequest(
        segment_key="segment",
        generated_by="release-pipeline",
        baseline_records=[
            {
                "application_id": "APP-1",
                "decision": "APPROVE",
                "risk_tier": "B",
                "is_approved": True,
                "triggered_reason_keys": [],
                "evaluation_attributes": {"segment": "A"},
            },
            {
                "application_id": "APP-2",
                "decision": "APPROVE",
                "risk_tier": "B",
                "is_approved": True,
                "triggered_reason_keys": [],
                "evaluation_attributes": {"segment": "B"},
            },
        ],
        current_records=[
            {
                "application_id": "APP-3",
                "decision": "DECLINE",
                "risk_tier": "F",
                "is_approved": False,
                "triggered_reason_keys": ["BANKRUPTCY_RECENT", "DTI_HIGH"],
                "evaluation_attributes": {"segment": "B"},
            },
            {
                "application_id": "APP-4",
                "decision": "DECLINE",
                "risk_tier": "F",
                "is_approved": False,
                "triggered_reason_keys": ["BANKRUPTCY_RECENT", "EXPOSURE_HIGH"],
                "evaluation_attributes": {"segment": "B"},
            },
        ],
    )


@pytest.mark.anyio
async def test_generate_snapshot_persists_monitoring_run():
    service = build_service()

    response = await service.generate_snapshot(build_request())

    assert response.segment_key == "segment"
    assert response.generated_by == "release-pipeline"
    assert response.thresholds["approval_rate_change_abs"] == DEFAULT_ALERT_THRESHOLDS["approval_rate_change_abs"]
    assert response.alert_count >= 1
    assert service.snapshot_repo.created[0]["segment_key"] == "segment"


@pytest.mark.anyio
async def test_get_latest_snapshot_returns_summary():
    service = build_service()
    await service.generate_snapshot(build_request())

    summary = await service.get_latest_snapshot("segment")

    assert summary.latest_snapshot is not None
    assert summary.latest_snapshot.segment_key == "segment"
    assert summary.latest_snapshot.alert_count >= 1


@pytest.mark.anyio
async def test_get_latest_snapshot_returns_empty_summary_when_missing():
    service = build_service()

    summary = await service.get_latest_snapshot("missing-segment")

    assert summary.segment_key == "missing-segment"
    assert summary.latest_snapshot is None
