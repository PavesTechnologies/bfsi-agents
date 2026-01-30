import httpx
from src.models.callback import CallbackPayload
import logging


logger = logging.getLogger(__name__)


class CallbackSender:
    @staticmethod
    async def send(url: str, payload: CallbackPayload):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                json=payload.model_dump(mode="json"),
                headers={"Content-Type": "application/json"},
            )

        logger.info(
            "callback_sent",
            extra={
                "callback_url": url,
                "status_code": response.status_code,
                "request_id": payload.request_id,
            },
        )

        response.raise_for_status()