"""Employer Verification adapter interfaces."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EmployerInput:
    """Input contract for employer verification."""
    employer_name: str
    employer_phone: Optional[str] = None
    employer_address: Optional[str] = None


@dataclass(frozen=True)
class EmployerVerificationResult:
    """Output contract for employer verification."""
    verified: bool
    normalized_name: Optional[str] = None
    naics_code: Optional[str] = None
    confidence: float = 0.0
