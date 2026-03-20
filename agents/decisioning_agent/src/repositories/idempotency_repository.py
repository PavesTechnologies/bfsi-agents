from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.underwriting_idempotency import UnderwritingIdempotency


class UnderwritingIdempotencyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, application_id: str):
        stmt = select(UnderwritingIdempotency).where(
            UnderwritingIdempotency.application_id == application_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, application_id: str, request_hash: str):
        record = UnderwritingIdempotency(
            application_id=application_id,
            request_hash=request_hash,
            status="PROCESSING",
        )
        self.session.add(record)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        return record

    async def reset_processing(self, application_id: str, request_hash: str):
        stmt = (
            update(UnderwritingIdempotency)
            .where(UnderwritingIdempotency.application_id == application_id)
            .values(
                request_hash=request_hash,
                status="PROCESSING",
                response_payload=None,
                error_message=None,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def mark_completed(self, application_id: str, response_payload: dict):
        stmt = (
            update(UnderwritingIdempotency)
            .where(UnderwritingIdempotency.application_id == application_id)
            .values(
                status="COMPLETED",
                response_payload=response_payload,
                error_message=None,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def mark_failed(self, application_id: str, error_message: str):
        stmt = (
            update(UnderwritingIdempotency)
            .where(UnderwritingIdempotency.application_id == application_id)
            .values(
                status="FAILED",
                error_message=error_message,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
