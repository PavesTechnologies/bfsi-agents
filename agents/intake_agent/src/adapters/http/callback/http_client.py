"""
Shared HTTP client for the entire application.

Rules:
- Single reusable async client
- Created once at startup
- Closed on shutdown
- Used by callback service and external adapters
"""

import httpx


class HTTPClient:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    # ---------- lifecycle ----------
    async def startup(self):
        """Create reusable connection pool"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            headers={"Content-Type": "application/json"},
        )

    async def shutdown(self):
        """Gracefully close connections"""
        if self._client:
            await self._client.aclose()

    # ---------- HTTP methods ----------
    async def get(self, url: str, **kwargs):
        self._ensure_client()
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, **kwargs):
        self._ensure_client()
        return await self._client.post(url, **kwargs)

    async def put(self, url: str, **kwargs):
        self._ensure_client()
        return await self._client.put(url, **kwargs)

    async def delete(self, url: str, **kwargs):
        self._ensure_client()
        return await self._client.delete(url, **kwargs)

    # ---------- internal ----------
    def _ensure_client(self):
        if self._client is None:
            raise RuntimeError("HTTP client not initialized. Call startup() first.")


# global singleton
http_client = HTTPClient()
