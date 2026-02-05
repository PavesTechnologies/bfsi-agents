"""Email Domain Risk adapter interfaces."""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class EmailInput:
    """Input contract for email domain risk analysis."""
    email: str


@dataclass(frozen=True)
class EmailRiskResult:
    """Output contract for email domain risk analysis."""
    domain: str
    risk: Literal["low", "medium", "high"]
    disposable: bool
    confidence: float
