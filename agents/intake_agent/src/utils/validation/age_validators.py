"""Age-related, non-blocking validators.

These functions return ValidationResult and never raise exceptions so higher
layers can decide how to act on failure reasons.
"""
from __future__ import annotations

import datetime

from .results import ValidationResult


def validate_minimum_age(dob: datetime.date, minimum_age: int = 18) -> ValidationResult:
    """Validate that a date of birth corresponds to an age >= `minimum_age`.

    Rules:
      - If `dob` is not a `datetime.date` instance => invalid
      - If `dob` is in the future => invalid
      - Age is calculated from today's date (no timezone handling)
      - Returns ValidationResult with field='date_of_birth'
    """
    field_name = "date_of_birth"
    try:
        if not isinstance(dob, datetime.date):
            return ValidationResult(field=field_name, is_valid=False, reason="date_of_birth must be a date")

        today = datetime.date.today()
        if dob > today:
            return ValidationResult(field=field_name, is_valid=False, reason="date_of_birth cannot be in the future")

        # Calculate age correctly accounting for birth month/day
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        if age < minimum_age:
            return ValidationResult(
                field=field_name,
                is_valid=False,
                reason=f"applicant must be at least {minimum_age} years old (calculated age: {age})",
            )

        return ValidationResult(field=field_name, is_valid=True)
    except Exception as exc:  # pragma: no cover - defensive
        return ValidationResult(field=field_name, is_valid=False, reason=f"validation error: {exc}")
