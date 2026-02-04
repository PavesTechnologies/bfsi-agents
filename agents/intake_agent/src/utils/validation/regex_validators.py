"""Non-blocking regex and simple logical validators.

Each function returns a ValidationResult and never raises exceptions. They are
intended to be pure utilities that higher-level code can call and decide how to
act on failures.
"""
from __future__ import annotations

import datetime
import re
from typing import Optional

from .results import ValidationResult


_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_ssn_last4(value: Optional[str]) -> ValidationResult:
    """Valid if value is None or exactly 4 digits.

    Missing (None) is treated as valid per non-blocking rule for optional
    fields.
    """
    field_name = "ssn_last4"
    try:
        if value is None:
            return ValidationResult(field=field_name, is_valid=True)
        if not isinstance(value, str):
            return ValidationResult(field=field_name, is_valid=False, reason="ssn_last4 must be a string of 4 digits")
        if re.fullmatch(r"\d{4}", value.strip()):
            return ValidationResult(field=field_name, is_valid=True)
        return ValidationResult(field=field_name, is_valid=False, reason="ssn_last4 must be exactly 4 digits")
    except Exception as exc:  # pragma: no cover - defensive
        return ValidationResult(field=field_name, is_valid=False, reason=f"validation error: {exc}")


def validate_email(value: str) -> ValidationResult:
    """Basic email format check using a lightweight regex.

    This validator does not guarantee deliverability; it only checks shape.
    """
    field_name = "email"
    try:
        if not isinstance(value, str):
            return ValidationResult(field=field_name, is_valid=False, reason="email must be a string")
        value = value.strip()
        if not value:
            return ValidationResult(field=field_name, is_valid=False, reason="email must not be empty")
        if _EMAIL_RE.fullmatch(value):
            return ValidationResult(field=field_name, is_valid=True)
        return ValidationResult(field=field_name, is_valid=False, reason="invalid email format")
    except Exception as exc:  # pragma: no cover - defensive
        return ValidationResult(field=field_name, is_valid=False, reason=f"validation error: {exc}")


def validate_phone(value: str) -> ValidationResult:
    """Phone is valid when 10 to 15 digits remain after stripping non-numeric characters."""
    field_name = "phone"
    try:
        if not isinstance(value, str):
            return ValidationResult(field=field_name, is_valid=False, reason="phone must be a string")
        digits = re.sub(r"\D", "", value)
        length = len(digits)
        if 10 <= length <= 15:
            return ValidationResult(field=field_name, is_valid=True)
        return ValidationResult(field=field_name, is_valid=False, reason="phone must contain 10 to 15 digits after removing non-numeric characters")
    except Exception as exc:  # pragma: no cover - defensive
        return ValidationResult(field=field_name, is_valid=False, reason=f"validation error: {exc}")


def validate_dob(value: datetime.date) -> ValidationResult:
    """Valid if the date is not in the future. Accepts datetime.date instances.

    The function will not attempt to compute age or apply domain rules.
    """
    field_name = "date_of_birth"
    try:
        if not isinstance(value, datetime.date):
            return ValidationResult(field=field_name, is_valid=False, reason="date_of_birth must be a date")
        today = datetime.date.today()
        if value <= today:
            return ValidationResult(field=field_name, is_valid=True)
        return ValidationResult(field=field_name, is_valid=False, reason="date_of_birth cannot be in the future")
    except Exception as exc:  # pragma: no cover - defensive
        return ValidationResult(field=field_name, is_valid=False, reason=f"validation error: {exc}")
