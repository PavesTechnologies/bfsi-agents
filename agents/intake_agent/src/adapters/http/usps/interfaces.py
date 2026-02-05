"""USPS Address Verification adapter interfaces."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class USPSAddressInput:
    """Input contract for USPS address verification."""
    address_line1: str
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


@dataclass(frozen=True)
class USPSAddressResult:
    """Output contract for USPS address verification."""
    deliverable: bool
    standardized_address: Optional[str] = None
    zip5: Optional[str] = None
    zip4: Optional[str] = None
    confidence: float = 0.0
