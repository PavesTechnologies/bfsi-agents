"""USPS Address Verification adapter interfaces."""

from dataclasses import dataclass


@dataclass(frozen=True)
class USPSAddressInput:
    """Input contract for USPS address verification."""

    address_line1: str
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None


@dataclass(frozen=True)
class USPSAddressResult:
    """Output contract for USPS address verification."""

    deliverable: bool
    standardized_address: str | None = None
    zip5: str | None = None
    zip4: str | None = None
    confidence: float = 0.0
