"""
LOS Schema Validation

Deterministic validation against the LOS schema.
Raises domain-level exceptions with clear error messages.
"""

from typing import Any

from pydantic import ValidationError
from src.domain.output.los_schema import LOSOutput


class LOSSchemaValidationError(Exception):
    """
    Domain-level exception raised when canonical output fails LOS schema validation.

    Attributes:
        message: Human-readable error message
        invalid_fields: List of field names that failed validation
        validation_errors: Raw validation error details
    """

    def __init__(
        self,
        message: str,
        invalid_fields: list[str] | None = None,
        validation_errors: list[dict[str, Any]] | None = None,
    ):
        self.message = message
        self.invalid_fields = invalid_fields or []
        self.validation_errors = validation_errors or []
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of error."""
        parts = [self.message]

        if self.invalid_fields:
            parts.append(f"Invalid fields: {', '.join(sorted(self.invalid_fields))}")

        if self.validation_errors:
            error_details = []
            for error in self.validation_errors:
                loc = " -> ".join(str(l) for l in error.get("loc", []))  # noqa: E741
                msg = error.get("msg", "Unknown error")
                error_details.append(f"  {loc}: {msg}")
            if error_details:
                parts.append("Details:\n" + "\n".join(error_details))

        return "\n".join(parts)


def validate_los_output(output: dict[str, Any]) -> None:
    """
    Validate canonical output against LOS schema.

    This function performs strict validation:
    - All required fields must be present
    - All fields must match their defined types
    - Unknown/extra fields are rejected
    - Nested structures are validated recursively

    Args:
        output: Dictionary to validate against LOSOutput schema

    Raises:
        LOSSchemaValidationError: If output does not conform to LOS schema

    Side Effects:
        None (pure validation function)
    """
    try:
        # Attempt to instantiate LOSOutput with the given output
        # Pydantic will perform all validation and raise ValidationError on failure
        LOSOutput(**output)

    except ValidationError as e:
        # Extract error information from Pydantic ValidationError
        raw_errors = e.errors()

        # Build list of invalid field names (top-level and nested)
        invalid_fields = set()
        for error_dict in raw_errors:
            loc = error_dict.get("loc", ())
            if loc:
                # First element in location tuple is the top-level field
                top_level_field = str(loc[0])
                invalid_fields.add(top_level_field)

        # Build error message
        error_count = len(raw_errors)
        message = f"LOS schema validation failed: {error_count} error(s)"

        # Raise domain exception with details
        raise LOSSchemaValidationError(
            message=message,
            invalid_fields=sorted(list(invalid_fields)),
            validation_errors=raw_errors,
        ) from e
