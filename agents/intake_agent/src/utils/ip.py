"""Proxy-safe IP extraction utilities

Priority:
- X-Forwarded-For (first IP)
- X-Real-IP
- remote_addr (request.client.host)

This intentionally keeps logic minimal and focused.
"""
from typing import Optional


def extract_ip(headers: dict[str, str], remote_addr: Optional[str] = None) -> str:
    """Extract client IP using proxy-safe priority.

    Args:
        headers: dict of request headers (expected lower-case keys)
        remote_addr: fallback from request.client.host

    Returns:
        IP address string or 'unknown' when not available
    """
    # Normalize header keys to lower-case for safety
    hdr = {k.lower(): v for k, v in (headers or {}).items()}

    xff = hdr.get("x-forwarded-for")
    if xff:
        # take first IP in the list
        first = xff.split(",")[0].strip()
        if first:
            return first

    xr = hdr.get("x-real-ip")
    if xr:
        return xr.strip()

    if remote_addr:
        return remote_addr

    return "unknown"
