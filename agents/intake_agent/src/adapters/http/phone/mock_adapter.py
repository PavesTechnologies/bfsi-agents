"""Mock Phone Intelligence adapter."""

import re

from .interfaces import PhoneInput, PhoneIntelligenceResult


class MockPhoneAdapter:
    """Stateless mock phone intelligence adapter.

    No state, no database, no side effects.
    Deterministic mock behavior for testing.
    """

    @staticmethod
    def analyze_phone(phone_input: PhoneInput) -> PhoneIntelligenceResult:
        """Analyze phone number using mock logic.

        Mock behavior:
        - valid=True if >= 10 digits after stripping non-numeric characters
        - line_type="mobile" for deterministic testing

        Args:
            phone_input: Phone number to analyze

        Returns:
            PhoneIntelligenceResult with validation and line type info
        """
        if not phone_input.phone_number:
            return PhoneIntelligenceResult(valid=False, confidence=0.0)

        # Extract only digits
        digits_only = re.sub(r"\D", "", phone_input.phone_number)

        # Valid if at least 10 digits
        is_valid = len(digits_only) >= 10

        return PhoneIntelligenceResult(
            valid=is_valid,
            line_type="mobile" if is_valid else "unknown",
            carrier="Mock Carrier" if is_valid else None,
            confidence=0.92 if is_valid else 0.0,
        )
