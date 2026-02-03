from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update
from uuid import UUID

#from models.idempotency import IntakeIdempotency
from src.models.models import IntakeIdempotency


class IdempotencyRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, request_id: UUID):
        stmt = select(IntakeIdempotency).where(
            IntakeIdempotency.request_id == request_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        request_id: UUID,
        app_id: UUID,
        request_hash: str
    ):
        record = IntakeIdempotency(
            request_id=request_id,
            app_id=app_id,
            request_hash=request_hash,
            status="RECEIVED"
        )
        self.db.add(record)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

    async def mark_processing(self, request_id: UUID):
        await self._update_status(request_id, "PROCESSING")

    async def mark_completed(self, request_id: UUID, response_payload: dict):
        stmt = (
            update(IntakeIdempotency)
            .where(IntakeIdempotency.request_id == request_id)
            .values(
                status="COMPLETED",
                response_payload=response_payload
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def mark_failed(self, request_id: UUID):
        await self._update_status(request_id, "FAILED")

    async def _update_status(self, request_id: UUID, status: str):
        stmt = (
            update(IntakeIdempotency)
            .where(IntakeIdempotency.request_id == request_id)
            .values(status=status)
        )
        await self.db.execute(stmt)
        await self.db.commit()
