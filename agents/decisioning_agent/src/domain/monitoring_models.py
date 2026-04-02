"""Domain models for underwriting monitoring snapshots."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MonitoringSnapshotRequest(BaseModel):
    segment_key: str = Field(description="Evaluation attribute used for segment analysis")
    baseline_records: List[Dict[str, Any]]
    current_records: List[Dict[str, Any]]
    thresholds: Optional[Dict[str, float]] = None
    generated_by: Optional[str] = None


class MonitoringSnapshotResponse(BaseModel):
    run_id: str
    segment_key: str
    alert_count: int
    high_severity_alert_count: int
    report: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    thresholds: Dict[str, float]
    generated_by: Optional[str] = None
    created_at: datetime


class MonitoringSnapshotSummary(BaseModel):
    segment_key: str
    latest_snapshot: Optional[MonitoringSnapshotResponse] = None
