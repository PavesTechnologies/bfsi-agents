"""Phone Intelligence adapter interfaces."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PhoneInput:
    """Input contract for phone intelligence."""

    phone_number: str


@dataclass(frozen=True)
class PhoneIntelligenceResult:
    """Output contract for phone intelligence."""

    valid: bool
    line_type: Literal["mobile", "unknown"] = "unknown"
    carrier: str | None = None
    confidence: float = 0.0
