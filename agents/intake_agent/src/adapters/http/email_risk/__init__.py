"""Email Domain Risk adapter."""
from .interfaces import EmailInput, EmailRiskResult
from .mock_adapter import MockEmailAdapter

__all__ = [
    "EmailInput",
    "EmailRiskResult",
    "MockEmailAdapter",
]
