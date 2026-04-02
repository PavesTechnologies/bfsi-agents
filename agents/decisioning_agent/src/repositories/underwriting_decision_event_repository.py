from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.underwriting_decision_event import UnderwritingDecisionEvent


class UnderwritingDecisionEventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(
        self,
        *,
        application_id: str,
        underwriting_decision_id: str | None,
        event_type: str,
        event_status: str | None,
        actor: str | None,
        event_payload: dict | None,
        notes: str | None = None,
    ) -> UnderwritingDecisionEvent:
        event = UnderwritingDecisionEvent(
            application_id=application_id,
            underwriting_decision_id=underwriting_decision_id,
            event_type=event_type,
            event_status=event_status,
            actor=actor,
            event_payload=event_payload,
            notes=notes,
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_events_for_application(self, application_id: str) -> list[UnderwritingDecisionEvent]:
        stmt = (
            select(UnderwritingDecisionEvent)
            .where(UnderwritingDecisionEvent.application_id == application_id)
            .order_by(UnderwritingDecisionEvent.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
