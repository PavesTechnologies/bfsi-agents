from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.underwriting_monitoring_snapshot import UnderwritingMonitoringSnapshot


class UnderwritingMonitoringSnapshotRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_snapshot(
        self,
        *,
        segment_key: str,
        generated_by: str | None,
        thresholds: dict,
        report: dict,
        alerts: list[dict],
        baseline_records: list[dict],
        current_records: list[dict],
        notes: str | None = None,
    ) -> UnderwritingMonitoringSnapshot:
        snapshot = UnderwritingMonitoringSnapshot(
            segment_key=segment_key,
            generated_by=generated_by,
            thresholds=thresholds,
            report=report,
            alerts=alerts,
            baseline_records=baseline_records,
            current_records=current_records,
            notes=notes,
        )
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot

    async def get_latest_snapshot(
        self,
        segment_key: str,
    ) -> UnderwritingMonitoringSnapshot | None:
        stmt = (
            select(UnderwritingMonitoringSnapshot)
            .where(UnderwritingMonitoringSnapshot.segment_key == segment_key)
            .order_by(UnderwritingMonitoringSnapshot.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
