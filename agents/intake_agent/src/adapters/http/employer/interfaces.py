"""Employer Verification adapter interfaces."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EmployerInput:
    """Input contract for employer verification."""

    employer_name: str
    employer_phone: str | None = None
    employer_address: str | None = None


@dataclass(frozen=True)
class EmployerVerificationResult:
    """Output contract for employer verification."""

    verified: bool
    normalized_name: str | None = None
    naics_code: str | None = None
    confidence: float = 0.0
