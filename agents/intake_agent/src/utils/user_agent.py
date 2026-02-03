"""User-Agent parsing using the `ua-parser` library.

No regexes — rely on the library for accurate parsing.
"""
from typing import Tuple
# from ua_parser.user_agent_parser import Parse


def parse_user_agent(user_agent: str) -> Tuple[str, str, str]:
    """Parse user-agent and return (browser, os, device_type)

    device_type is one of: 'mobile', 'tablet', 'desktop', 'unknown'
    """
    if not user_agent:
        return "unknown", "unknown", "unknown"

    try:
        ua = Parse(user_agent)
    except Exception:
        return "unknown", "unknown", "unknown"

    browser_family = ua.get("user_agent", {}).get("family", "unknown")
    os_family = ua.get("os", {}).get("family", "unknown")
    device_family = ua.get("device", {}).get("family", "unknown")

    # Determine device type based on device family
    device_family_lower = device_family.lower()
    if any(x in device_family_lower for x in ["mobile", "phone"]):
        device_type = "mobile"
    elif any(x in device_family_lower for x in ["tablet", "ipad", "kindle"]):
        device_type = "tablet"
    elif "other" in device_family_lower or device_family == "Other":
        # Check for common tablet/mobile user agents
        ua_lower = user_agent.lower()
        if any(x in ua_lower for x in ["ipad", "tablet", "kindle"]):
            device_type = "tablet"
        elif any(x in ua_lower for x in ["mobile", "phone", "android"]):
            device_type = "mobile"
        else:
            device_type = "desktop"
    else:
        device_type = "desktop"

    return browser_family, os_family, device_type
