"""Central MetadataService that extracts metadata from a request.

All header parsing and UA/ip handling should go through this class so the
API layer doesn't touch headers directly.
"""
from fastapi import Request
from typing import Optional

from src.utils.ip import extract_ip
from src.utils.user_agent import parse_user_agent
from src.models.metadata import RequestMetadata


class MetadataService:
    @staticmethod
    async def extract(request: Request) -> RequestMetadata:
        """Extract RequestMetadata from a FastAPI/Starlette Request.

        Responsibilities:
        - Read headers (kept here so routes don't access headers directly)
        - Determine IP using proxy-safe priority
        - Parse user-agent using `user-agents` library
        - Read `accept-language` and `referer`/`referrer` headers
        """
        headers = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in request.scope.get("headers", [])}
        # Make a dict with lower-case keys for convenience
        headers_lower = {k.lower(): v for k, v in headers.items()}

        remote_addr = None
        if request.client:
            remote_addr = request.client.host

        ip = extract_ip(headers_lower, remote_addr=remote_addr)

        user_agent = headers_lower.get("user-agent")
        browser, os_name, device_type = parse_user_agent(user_agent or "")

        accept_language = headers_lower.get("accept-language")
        # Some clients use 'referer' spelling
        referrer = headers_lower.get("referer") or headers_lower.get("referrer")

        metadata = RequestMetadata(
            ip_address=ip,
            user_agent=user_agent,
            browser=browser,
            os=os_name,
            device_type=device_type,
            accept_language=accept_language,
            referrer=referrer,
        )

        return metadata
