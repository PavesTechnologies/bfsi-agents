from sqlalchemy.ext.asyncio import AsyncSession

from src.models.disbursement_transition import DisbursementTransitionLog


class DisbursementTransitionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_transition(
        self,
        *,
        application_id: str,
        correlation_id: str | None,
        from_status: str | None,
        to_status: str,
        reason: str | None,
        transition_metadata: dict | None,
    ) -> None:
        log = DisbursementTransitionLog(
            application_id=application_id,
            correlation_id=correlation_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            transition_metadata=transition_metadata,
        )
        self.session.add(log)
        await self.session.commit()
