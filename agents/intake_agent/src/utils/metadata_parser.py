"""
Metadata extraction from HTTP headers

Handles:
- IP address extraction (including proxy headers)
- Device and browser information parsing
- User agent analysis
"""

import re
from dataclasses import dataclass
from enum import StrEnum


class DeviceType(StrEnum):
    """Enumeration of device types"""

    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    UNKNOWN = "unknown"


@dataclass
class DeviceMetadata:
    """Device and browser information"""

    device_type: DeviceType
    browser: str
    browser_version: str
    os: str
    os_version: str
    user_agent: str


@dataclass
class RequestMetadata:
    """Complete request metadata"""

    ip_address: str
    device: DeviceMetadata
    raw_user_agent: str


class MetadataParser:
    """Extract and parse metadata from HTTP headers"""

    # IP extraction patterns for common proxy headers
    PROXY_HEADERS = [
        "x-forwarded-for",  # Standard de-facto proxy header
        "cf-connecting-ip",  # Cloudflare
        "x-real-ip",  # Nginx
        "x-client-ip",  # General proxy
        "x-forwarded-host",
        "x-original-forwarded-for",
    ]

    # User agent patterns for device detection
    DEVICE_PATTERNS = {
        "mobile": [
            r"(iphone|ipod|android.*mobile|blackberry|windows phone|webos)",
            r"mobile",
            r"mobi",
        ],
        "tablet": [
            r"(ipad|android(?!.*mobile)|kindle|playbook|nexus 7|nexus 10|xoom|silk)",
            r"tablet",
        ],
    }

    # Browser detection patterns
    BROWSER_PATTERNS = {
        "Chrome": r"(?:Chrome|Chromium|CriOS)[/\s]([0-9.]+)",
        "Firefox": r"Firefox[/\s]([0-9.]+)",
        "Safari": r"Version[/\s]([0-9.]+).*Safari",
        "Edge": r"Edg[e|A][/\s]([0-9.]+)",
        "Opera": r"(?:Opera|OPR)[/\s]([0-9.]+)",
        "IE": r"(?:MSIE|rv:)([0-9.]+)",
    }

    # OS detection patterns
    OS_PATTERNS = {
        "Windows": {
            "pattern": r"Windows NT ([0-9.]+)",
            "versions": {
                "10.0": "10",
                "6.3": "8.1",
                "6.2": "8",
                "6.1": "7",
                "6.0": "Vista",
                "5.2": "Server 2003",
                "5.1": "XP",
            },
        },
        "macOS": {
            "pattern": r"Mac OS X ([0-9_.]+)",
            "versions": {},  # Versions are as-is in user agent
        },
        "iOS": {
            "pattern": r"(?:iPhone|iPad|iPod).*OS ([0-9_]+)",
            "versions": {},
        },
        "Android": {
            "pattern": r"Android[;\s]([0-9.]+)",
            "versions": {},
        },
        "Linux": {
            "pattern": r"Linux",
            "versions": {},
        },
    }

    @staticmethod
    def extract_ip(headers: dict[str, str], remote_addr: str | None = None) -> str:
        """
        Extract client IP address from headers, checking proxy headers first.

        Args:
            headers: HTTP headers dictionary
            remote_addr: Fallback IP address from socket

        Returns:
            Client IP address

        Examples:
            >>> headers = {"x-forwarded-for": "203.0.113.5, 198.51.100.2"}
            >>> MetadataParser.extract_ip(headers)
            '203.0.113.5'
        """
        # Check proxy headers
        for header in MetadataParser.PROXY_HEADERS:
            if header in headers:
                value = headers[header]
                # Handle comma-separated IPs (x-forwarded-for format)
                if "," in value:
                    # Take first IP as it's the original client
                    ip = value.split(",")[0].strip()
                else:
                    ip = value.strip()

                # Validate IP format (basic check)
                if MetadataParser._is_valid_ip(ip):
                    return ip

        # Fallback to remote address from connection
        if remote_addr and MetadataParser._is_valid_ip(remote_addr):
            return remote_addr

        return "unknown"

    @staticmethod
    def extract_device_metadata(user_agent: str) -> DeviceMetadata:
        """
        Extract device and browser information from user agent string.

        Args:
            user_agent: HTTP User-Agent header value

        Returns:
            DeviceMetadata containing device type, browser, OS info

        Examples:
            >>> ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
            >>> metadata = MetadataParser.extract_device_metadata(ua)
            >>> metadata.device_type
            <DeviceType.DESKTOP: 'desktop'>
        """
        device_type = MetadataParser._detect_device_type(user_agent)
        browser, browser_version = MetadataParser._detect_browser(user_agent)
        os, os_version = MetadataParser._detect_os(user_agent)

        return DeviceMetadata(
            device_type=device_type,
            browser=browser,
            browser_version=browser_version,
            os=os,
            os_version=os_version,
            user_agent=user_agent,
        )

    @staticmethod
    def extract_metadata(
        headers: dict[str, str],
        user_agent: str,
        remote_addr: str | None = None,
    ) -> RequestMetadata:
        """
        Extract complete request metadata from headers.

        Args:
            headers: HTTP headers dictionary
            user_agent: HTTP User-Agent header
            remote_addr: Remote address from socket connection

        Returns:
            RequestMetadata containing IP and device information

        Examples:
            >>> headers = {"user-agent": "Mozilla/5.0...", "x-forwarded-for": "1.2.3.4"}
            >>> metadata = MetadataParser.extract_metadata(headers, headers["user-agent"])
            >>> metadata.ip_address
            '1.2.3.4'
        """  # noqa: E501
        ip_address = MetadataParser.extract_ip(headers, remote_addr)
        device_metadata = MetadataParser.extract_device_metadata(user_agent)

        return RequestMetadata(
            ip_address=ip_address,
            device=device_metadata,
            raw_user_agent=user_agent,
        )

    @staticmethod
    def _detect_device_type(user_agent: str) -> DeviceType:
        """Detect device type from user agent"""
        ua_lower = user_agent.lower()

        for pattern in MetadataParser.DEVICE_PATTERNS["mobile"]:
            if re.search(pattern, ua_lower):
                return DeviceType.MOBILE

        for pattern in MetadataParser.DEVICE_PATTERNS["tablet"]:
            if re.search(pattern, ua_lower):
                return DeviceType.TABLET

        return DeviceType.DESKTOP

    @staticmethod
    def _detect_browser(user_agent: str) -> tuple[str, str]:
        """Detect browser and version from user agent"""
        for browser, pattern in MetadataParser.BROWSER_PATTERNS.items():
            match = re.search(pattern, user_agent)
            if match:
                version = match.group(1) if match.lastindex else "unknown"
                return browser, version

        return "unknown", "unknown"

    @staticmethod
    def _detect_os(user_agent: str) -> tuple[str, str]:
        """Detect OS and version from user agent"""
        for os_name, os_info in MetadataParser.OS_PATTERNS.items():
            pattern = os_info["pattern"]
            match = re.search(pattern, user_agent)

            if match:
                version_string = match.group(1) if match.lastindex else ""

                # Apply version mapping if available
                if os_info["versions"] and version_string in os_info["versions"]:
                    version = os_info["versions"][version_string]
                else:
                    # Clean up version string (replace _ with .)
                    version = (
                        version_string.replace("_", ".")
                        if version_string
                        else "unknown"
                    )

                return os_name, version

        return "unknown", "unknown"

    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Basic IP address validation (IPv4 and IPv6)"""
        # IPv4 validation
        ipv4_pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
        if re.match(ipv4_pattern, ip):
            parts = ip.split(".")
            return all(0 <= int(part) <= 255 for part in parts)

        # IPv6 validation (simplified)
        ipv6_pattern = r"^(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"
        return bool(re.match(ipv6_pattern, ip))
