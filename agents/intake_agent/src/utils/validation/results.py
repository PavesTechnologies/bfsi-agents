"""Validation result types used by validators.

Lightweight, dataclass-based result to keep validation non-blocking and
easy to consume in higher-level layers.
"""

from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Represents the result of a single field validation.

    Attributes:
        field: The name of the field validated (e.g., 'email', 'ssn_last4').
        is_valid: True when the value is considered valid, False otherwise.
        reason: Optional human-friendly explanation for a failure.
    """

    field: str
    is_valid: bool
    reason: str | None = None
