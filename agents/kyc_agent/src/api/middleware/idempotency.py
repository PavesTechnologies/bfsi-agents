# src/api/middleware/idempotency.py

import json
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.repositories.idempotency_repository import RedisIdempotencyRepository
from src.utils.hash_utils import generate_payload_hash


class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, repository: RedisIdempotencyRepository):
        super().__init__(app)
        self.repository = repository

    async def dispatch(self, request: Request, call_next: Callable):
        if request.method != "POST":
            return await call_next(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            return JSONResponse(
                status_code=400,
                content={"detail": "X-Idempotency-Key header required"},
            )

        body_bytes = await request.body()
        if not body_bytes:
            return JSONResponse(status_code=400, content={"detail": "Empty body"})

        try:
            payload = json.loads(body_bytes)
        except json.JSONDecodeError:
            return JSONResponse(status_code=400, content={"detail": "Invalid JSON"})

        payload_hash = generate_payload_hash(payload)

        # Attach to request.state
        request.state.idempotency_key = idempotency_key
        request.state.payload_hash = payload_hash
        request.state.application_id = payload.get("application_id")

        # Acquire Redis distributed lock
        lock_acquired = await self.repository.acquire_lock(idempotency_key)

        if not lock_acquired:
            return JSONResponse(
                status_code=409,
                content={"detail": "Request is already being processed"},
            )

        try:
            response = await call_next(request)
            return response
        except Exception:
            # On crash, release lock
            await self.repository.release_lock(idempotency_key)
            raise
