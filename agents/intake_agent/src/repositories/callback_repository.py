from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.callback import CallbackStatus


class CallbackRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_if_not_exists(self, request_id: str, callback_url: str):
        query = text("""
            INSERT INTO callback_status (request_id, callback_url, status)
            VALUES (:request_id, :callback_url, :status)
            ON CONFLICT (request_id) DO NOTHING
        """)
        await self.session.execute(query, {
            "request_id": request_id,
            "callback_url": str(callback_url),
            "status": CallbackStatus.PENDING.value,
        })
        await self.session.commit()

    async def mark_sent(self, request_id: str) -> bool:
        query = text("""
            UPDATE callback_status
            SET status = :sent
            WHERE request_id = :request_id
              AND status = :pending
        """)
        result = await self.session.execute(query, {
            "sent": CallbackStatus.SENT.value,
            "pending": CallbackStatus.PENDING.value,
            "request_id": request_id,
        })
        await self.session.commit()
        return result.rowcount == 1

    async def get_callback_url(self, request_id: str) -> str:
        query = text("""
            SELECT callback_url FROM callback_status
            WHERE request_id = :request_id
        """)
        result = await self.session.execute(query, {"request_id": request_id})
        row = result.fetchone()
        return row[0] if row else None