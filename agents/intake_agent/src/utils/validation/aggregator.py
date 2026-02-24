"""Aggregation utilities for non-blocking intake validation.

Provides a simple summary object and a `validate_applicant` helper that runs a
set of field validators without raising exceptions or mutating the applicant.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .age_validators import validate_minimum_age
from .regex_validators import validate_dob, validate_email, validate_ssn_last4
from .results import ValidationResult


@dataclass
class ValidationSummary:
    """Summary of validation results for an applicant."""

    is_valid: bool
    results: list[ValidationResult] = field(default_factory=list)
    failed_fields: list[str] = field(default_factory=list)


def validate_applicant(applicant) -> ValidationSummary:
    """Run non-blocking validators for an ApplicantInfo-like object.

    The function is defensive: it never raises, never mutates the applicant and
    always returns a ValidationSummary containing individual ValidationResult
    objects. Missing attributes are passed through to validators which handle
    type and presence checks themselves.
    """
    results: list[ValidationResult] = []

    try:
        email = getattr(applicant, "email", None)
        ssn_last4 = getattr(applicant, "ssn_last4", None)
        dob = getattr(applicant, "date_of_birth", None)

        # Run validators individually and capture any unexpected errors as
        # failed ValidationResult entries so this function never raises.
        try:
            results.append(validate_email(email))
        except Exception as exc:  # pragma: no cover - defensive
            results.append(
                ValidationResult(
                    field="email", is_valid=False, reason=f"validation error: {exc}"
                )
            )

        try:
            results.append(validate_ssn_last4(ssn_last4))
        except Exception as exc:  # pragma: no cover - defensive
            results.append(
                ValidationResult(
                    field="ssn_last4", is_valid=False, reason=f"validation error: {exc}"
                )
            )

        try:
            results.append(validate_dob(dob))
        except Exception as exc:  # pragma: no cover - defensive
            results.append(
                ValidationResult(
                    field="date_of_birth",
                    is_valid=False,
                    reason=f"validation error: {exc}",
                )
            )

        try:
            results.append(validate_minimum_age(dob))
        except Exception as exc:  # pragma: no cover - defensive
            results.append(
                ValidationResult(
                    field="date_of_birth",
                    is_valid=False,
                    reason=f"validation error: {exc}",
                )
            )

        failed_fields = list(
            dict.fromkeys([r.field for r in results if not r.is_valid])
        )
        is_valid = all(r.is_valid for r in results)

        return ValidationSummary(
            is_valid=is_valid, results=results, failed_fields=failed_fields
        )

    except Exception as exc:  # pragma: no cover - defensive
        # Catch any unforeseen errors and return them as a failing summary
        fallback = ValidationResult(
            field="applicant", is_valid=False, reason=f"aggregator error: {exc}"
        )
        return ValidationSummary(
            is_valid=False, results=[fallback], failed_fields=["applicant"]
        )
