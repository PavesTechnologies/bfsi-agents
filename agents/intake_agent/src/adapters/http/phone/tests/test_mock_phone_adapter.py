"""Tests for mock phone adapter."""
import pytest
from src.adapters.http.phone.interfaces import PhoneInput
from src.adapters.http.phone.mock_adapter import MockPhoneAdapter


class TestMockPhoneAdapter:
    """Test suite for MockPhoneAdapter."""

    def test_analyze_phone_with_valid_us_number(self):
        """Valid US phone number should be marked as valid."""
        adapter = MockPhoneAdapter()
        result = adapter.analyze_phone(
            PhoneInput(phone_number="+1-555-0101000")
        )
        
        assert result.valid is True
        assert result.confidence == 0.92
        assert result.line_type == "mobile"
        assert result.carrier == "Mock Carrier"

    def test_analyze_phone_with_10_digits(self):
        """Phone with exactly 10 digits should be valid."""
        adapter = MockPhoneAdapter()
        result = adapter.analyze_phone(
            PhoneInput(phone_number="5550100000")
        )
        
        assert result.valid is True
        assert result.confidence == 0.92

    def test_analyze_phone_with_11_digits(self):
        """Phone with 11 digits should be valid."""
        adapter = MockPhoneAdapter()
        result = adapter.analyze_phone(
            PhoneInput(phone_number="15550100000")
        )
        
        assert result.valid is True
        assert result.confidence == 0.92

    def test_analyze_phone_with_formatted_number(self):
        """Formatted phone numbers should extract digits correctly."""
        adapter = MockPhoneAdapter()
        result = adapter.analyze_phone(
            PhoneInput(phone_number="(555) 010-0000")
        )
        
        assert result.valid is True
        assert result.confidence == 0.92

    def test_analyze_phone_with_9_digits(self):
        """Phone with less than 10 digits should be invalid."""
        adapter = MockPhoneAdapter()
        result = adapter.analyze_phone(
            PhoneInput(phone_number="555010000")
        )
        
        assert result.valid is False
        assert result.confidence == 0.0
        assert result.line_type == "unknown"
        assert result.carrier is None

    def test_analyze_phone_with_empty_string(self):
        """Empty phone number should be invalid."""
        adapter = MockPhoneAdapter()
        result = adapter.analyze_phone(
            PhoneInput(phone_number="")
        )
        
        assert result.valid is False
        assert result.confidence == 0.0
        assert result.carrier is None

    def test_analyze_phone_with_non_numeric_only(self):
        """Non-numeric only strings should be invalid."""
        adapter = MockPhoneAdapter()
        result = adapter.analyze_phone(
            PhoneInput(phone_number="()- ")
        )
        
        assert result.valid is False
        assert result.confidence == 0.0

    def test_analyze_phone_with_mixed_content(self):
        """Digits mixed with letters should extract digits."""
        adapter = MockPhoneAdapter()
        result = adapter.analyze_phone(
            PhoneInput(phone_number="5A5A5B0B1B0B1B0B0B0")
        )
        
        assert result.valid is True
        assert result.confidence == 0.92

    def test_analyze_phone_output_shape(self):
        """Result should have all expected fields."""
        adapter = MockPhoneAdapter()
        result = adapter.analyze_phone(
            PhoneInput(phone_number="5551234567")
        )
        
        # Check all fields exist
        assert hasattr(result, "valid")
        assert hasattr(result, "line_type")
        assert hasattr(result, "carrier")
        assert hasattr(result, "confidence")
        
        # Check types
        assert isinstance(result.valid, bool)
        assert isinstance(result.confidence, float)
        assert result.line_type in ["mobile", "unknown"]
        assert 0.0 <= result.confidence <= 1.0

    def test_adapter_is_stateless(self):
        """Multiple calls should return consistent results."""
        adapter = MockPhoneAdapter()
        input_data = PhoneInput(phone_number="2025550100")
        
        result1 = adapter.analyze_phone(input_data)
        result2 = adapter.analyze_phone(input_data)
        
        assert result1.valid == result2.valid
        assert result1.confidence == result2.confidence
        assert result1.line_type == result2.line_type

    def test_analyze_phone_with_plus_sign(self):
        """Phone number with international plus should work."""
        adapter = MockPhoneAdapter()
        result = adapter.analyze_phone(
            PhoneInput(phone_number="+1 555 0101 000")
        )
        
        assert result.valid is True

    def test_analyze_phone_no_exceptions(self):
        """Should handle edge cases without raising exceptions."""
        adapter = MockPhoneAdapter()
        
        # Very long string with some digits
        long_input = "A" * 1000 + "5550100000"
        result = adapter.analyze_phone(
            PhoneInput(phone_number=long_input)
        )
        assert result.valid is True
        
        # Special characters mixed with numbers
        special_input = "!!!5!!5!!5!!0!!1!!0!!0!!0!!0!!0!!"
        result = adapter.analyze_phone(
            PhoneInput(phone_number=special_input)
        )
        assert result.valid is True
