import os
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")

from src.services.monitoring.snapshot_job import run_monitoring_snapshot_job


class FakeUnderwritingRepository:
    async def get_monitoring_payloads(self, *, date_from, date_to, evaluation_attributes=None):
        return [
            {
                "application_id": "APP-1",
                "decision": "DECLINE",
                "risk_tier": "F",
                "is_approved": False,
                "triggered_reason_keys": ["DTI_HIGH"],
                "evaluation_attributes": {"segment": "A"},
            }
        ]


class FakeSnapshotRepository:
    async def create_snapshot(self, **kwargs):
        return SimpleNamespace(id="snapshot-1", created_at=datetime.now(timezone.utc), **kwargs)


@pytest.mark.anyio
async def test_monitoring_snapshot_job_runs_end_to_end():
    result = await run_monitoring_snapshot_job(
        underwriting_repository=FakeUnderwritingRepository(),
        snapshot_repository=FakeSnapshotRepository(),
        segment_key="segment",
    )

    assert result["run_id"] == "snapshot-1"
