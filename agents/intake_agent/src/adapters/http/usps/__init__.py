"""USPS Address Verification adapter."""
from .interfaces import USPSAddressInput, USPSAddressResult
from .mock_adapter import MockUSPSAdapter

__all__ = [
    "USPSAddressInput",
    "USPSAddressResult",
    "MockUSPSAdapter",
]
