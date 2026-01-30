from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.callback_repository import CallbackRepository
from src.adapters.http.callback_sender import CallbackSender
from src.models.callback import CallbackPayload
import logging

logger = logging.getLogger(__name__)


class CallbackService:
    def __init__(self, session: AsyncSession):
        self.repo = CallbackRepository(session)

    async def send_success(self, request_id: str, data: dict):
        logger.info(
        "callback_send_success_called",
        extra={"request_id": request_id},)
        
        await self._send(
            request_id=request_id,
            status="SUCCESS",
            data=data,
            error=None,
        )

    async def send_failure(self, request_id: str, error: str):
        await self._send(
            request_id=request_id,
            status="FAILURE",
            data=None,
            error=error,
        )

    async def _send(self, request_id: str, status: str, data, error):
        callback_url = await self.repo.get_callback_url(request_id)
        if not callback_url:
            logger.error("callback_url_missing", extra={"request_id": request_id})
            return

        locked = await self.repo.mark_sent(request_id)
        if not locked:
            logger.warning("callback_already_sent", extra={"request_id": request_id})
            return

        payload = CallbackPayload(
            request_id=request_id,
            status=status,
            timestamp=datetime.utcnow(),
            data=data,
            error=error,
        )

        await CallbackSender.send(callback_url, payload)