import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from src.adapters.http.callback.callback_models import SuccessCallback
from src.adapters.http.callback.callback_client import (
    send_success_callback,
    CallbackDeliveryError,
)
from src.adapters.http.callback.callback_client import send_partial_success_callback

from src.adapters.http.callback.callback_models import PartialSuccessCallback


@pytest.mark.asyncio
async def test_send_success_callback_200(monkeypatch):
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_post.return_value = mock_response

    mock_client = MagicMock()
    mock_client.post = mock_post
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_client

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: mock_cm)

    payload = SuccessCallback(application_id="APP-1", data={"foo": "bar"})

    await send_success_callback("https://example.com/cb", payload)

    mock_post.assert_awaited_once()
    called_url = mock_post.call_args.kwargs.get("callback_url") if mock_post.call_args else None
    # verify called with correct url and json body
    assert mock_post.call_args[0][0] == "https://example.com/cb"
    assert mock_post.call_args[1]["json"]["status"] == "SUCCESS"
    assert mock_post.call_args[1]["json"]["application_id"] == "APP-1"


@pytest.mark.asyncio
async def test_send_success_callback_500(monkeypatch):
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Server Error"
    mock_post.return_value = mock_response

    mock_client = MagicMock()
    mock_client.post = mock_post
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_client

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: mock_cm)

    payload = SuccessCallback(application_id="APP-1", data={})

    with pytest.raises(CallbackDeliveryError):
        await send_success_callback("https://example.com/cb", payload)


@pytest.mark.asyncio
async def test_send_success_callback_timeout(monkeypatch):
    async def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("timeout")

    mock_post = AsyncMock(side_effect=raise_timeout)

    mock_client = MagicMock()
    mock_client.post = mock_post
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_client

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: mock_cm)

    payload = SuccessCallback(application_id="APP-1", data={})

    with pytest.raises(CallbackDeliveryError):
        await send_success_callback("https://example.com/cb", payload)


@pytest.mark.asyncio
async def test_send_partial_success_callback_200(monkeypatch):
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_post.return_value = mock_response

    mock_client = MagicMock()
    mock_client.post = mock_post
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_client

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: mock_cm)

    payload = PartialSuccessCallback(application_id="APP-1", warnings=["w1"], generated_at="2026-02-11T10:30:00Z")

    await send_partial_success_callback("https://example.com/partial", payload)

    mock_post.assert_awaited_once()
    assert mock_post.call_args[0][0] == "https://example.com/partial"
    assert mock_post.call_args[1]["json"]["status"] == "PARTIAL_SUCCESS"
    assert mock_post.call_args[1]["json"]["application_id"] == "APP-1"
    assert mock_post.call_args[1]["json"]["warnings"] == ["w1"]


@pytest.mark.asyncio
async def test_send_partial_success_callback_500(monkeypatch):
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Server Error"
    mock_post.return_value = mock_response

    mock_client = MagicMock()
    mock_client.post = mock_post
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_client

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: mock_cm)

    payload = PartialSuccessCallback(application_id="APP-1", warnings=[], generated_at="2026-02-11T10:30:00Z")

    with pytest.raises(CallbackDeliveryError):
        await send_partial_success_callback("https://example.com/partial", payload)


@pytest.mark.asyncio
async def test_send_partial_success_callback_timeout(monkeypatch):
    async def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("timeout")

    mock_post = AsyncMock(side_effect=raise_timeout)

    mock_client = MagicMock()
    mock_client.post = mock_post
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_client

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: mock_cm)

    payload = PartialSuccessCallback(application_id="APP-1", warnings=[], generated_at="2026-02-11T10:30:00Z")

    with pytest.raises(CallbackDeliveryError):
        await send_partial_success_callback("https://example.com/partial", payload)


@pytest.mark.asyncio
async def test_send_partial_success_callback_network_error(monkeypatch):
    async def raise_req_err(*args, **kwargs):
        raise httpx.RequestError("network")

    mock_post = AsyncMock(side_effect=raise_req_err)

    mock_client = MagicMock()
    mock_client.post = mock_post
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_client

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: mock_cm)

    payload = PartialSuccessCallback(application_id="APP-1", warnings=[], generated_at="2026-02-11T10:30:00Z")

    with pytest.raises(CallbackDeliveryError):
        await send_partial_success_callback("https://example.com/partial", payload)


@pytest.mark.asyncio
async def test_send_success_callback_network_error(monkeypatch):
    async def raise_req_err(*args, **kwargs):
        raise httpx.RequestError("network")

    mock_post = AsyncMock(side_effect=raise_req_err)

    mock_client = MagicMock()
    mock_client.post = mock_post
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_client

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: mock_cm)

    payload = SuccessCallback(application_id="APP-1", data={})

    with pytest.raises(CallbackDeliveryError):
        await send_success_callback("https://example.com/cb", payload)
