import pytest
from src.domain.validation.typed_field_validators import validate_first_name, validate_phone
from src.domain.validation.reason_codes import ValidationReasonCode

def test_tc_u1_validate_first_name_valid():
    """TC-U1: Name Regex - Valid: Letters, spaces, hyphens and apostrophes should pass."""
    valid_names = ["John", "Mary Jane", "O'Reilly", "Jean-Luc"]
    for name in valid_names:
        result = validate_first_name(name)
        assert result.passed is True, f"Failed for name: {name}"

def test_tc_u2_validate_first_name_invalid():
    """TC-U2: Name Regex - Invalid: Numbers and special characters should fail."""
    invalid_names = ["John123", "Mar@y", "Jane!", "12345"]
    for name in invalid_names:
        result = validate_first_name(name)
        assert result.passed is False, f"Should have failed for name: {name}"
        assert result.reason_code == ValidationReasonCode.INVALID_FIRST_NAME

def test_tc_u3_validate_phone_invalid_format():
    """TC-U3: Phone - Invalid Format: Missing +1 prefix or incorrect digit count should fail."""
    invalid_phones = [
        "1234567890",    # Missing +1
        "+1123456789",   # Too short (9 digits)
        "+112345678901", # Too long (11 digits)
        "+21234567890",   # Incorrect country code
        "abc1234567"     # Non-numeric
    ]
    for phone in invalid_phones:
        result = validate_phone(phone)
        assert result.passed is False, f"Should have failed for phone: {phone}"
        assert result.reason_code == ValidationReasonCode.INVALID_PHONE_FORMAT
