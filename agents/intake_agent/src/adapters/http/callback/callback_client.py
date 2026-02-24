from typing import Any

import httpx


class CallbackDeliveryError(Exception):
    """Raised when callback delivery fails."""


async def send_success_callback(
    callback_url: str, payload: Any, timeout: float = 5.0
) -> None:
    """
    Send a success callback to the given URL with the provided payload.

    Args:
        callback_url: Destination URL
        payload: SuccessCallback dataclass or dict-like with application_id and data
        timeout: Request timeout in seconds

    Raises:
        CallbackDeliveryError: on network, timeout, or non-2xx responses
    """
    # Prepare JSON body
    if hasattr(payload, "__dict__"):
        body = {
            "status": getattr(payload, "status", "SUCCESS"),
            "application_id": getattr(payload, "application_id", None),
            "data": getattr(payload, "data", None),
        }
    elif isinstance(payload, dict):
        body = payload
    else:
        body = dict(payload)

    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(callback_url, json=body, headers=headers)

            if not (200 <= response.status_code < 300):
                raise CallbackDeliveryError(
                    f"Callback delivery failed with status\
                          {response.status_code}: {response.text}"
                )

    except (httpx.RequestError, httpx.TimeoutException) as exc:
        raise CallbackDeliveryError(f"Callback delivery error: {exc}") from exc


async def send_partial_success_callback(
    callback_url: str, payload: Any, timeout: float = 5.0
) -> None:
    """
    Send a partial success callback with warnings and generated_at.

    JSON body:
    {
      "status": "PARTIAL_SUCCESS",
      "application_id": payload.application_id,
      "warnings": payload.warnings,
      "generated_at": payload.generated_at
    }
    """
    if hasattr(payload, "__dict__"):
        body = {
            "status": getattr(payload, "status", "PARTIAL_SUCCESS"),
            "application_id": getattr(payload, "application_id", None),
            "warnings": getattr(payload, "warnings", None),
            "generated_at": getattr(payload, "generated_at", None),
        }
    elif isinstance(payload, dict):
        body = payload
    else:
        body = dict(payload)

    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(callback_url, json=body, headers=headers)

            if not (200 <= response.status_code < 300):
                raise CallbackDeliveryError(
                    f"Callback delivery failed with status \
                        {response.status_code}: {response.text}"
                )

    except (httpx.RequestError, httpx.TimeoutException) as exc:
        raise CallbackDeliveryError(f"Callback delivery error: {exc}") from exc
