"""Phone Intelligence adapter."""
from .interfaces import PhoneInput, PhoneIntelligenceResult
from .mock_adapter import MockPhoneAdapter

__all__ = [
    "PhoneInput",
    "PhoneIntelligenceResult",
    "MockPhoneAdapter",
]
