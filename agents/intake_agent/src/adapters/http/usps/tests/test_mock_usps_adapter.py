"""Tests for mock USPS adapter."""
import pytest
from src.adapters.http.usps.interfaces import USPSAddressInput
from src.adapters.http.usps.mock_adapter import MockUSPSAdapter


class TestMockUSPSAdapter:
    """Test suite for MockUSPSAdapter."""

    def test_verify_address_with_empty_address_line(self):
        """Empty address line should return not deliverable."""
        adapter = MockUSPSAdapter()
        result = adapter.verify_address(
            USPSAddressInput(address_line1="")
        )
        
        assert result.deliverable is False
        assert result.confidence == 0.0
        assert result.zip4 is None
        assert result.standardized_address is None

    def test_verify_address_with_whitespace_only(self):
        """Whitespace-only address line should return not deliverable."""
        adapter = MockUSPSAdapter()
        result = adapter.verify_address(
            USPSAddressInput(address_line1="   ")
        )
        
        assert result.deliverable is False
        assert result.confidence == 0.0

    def test_verify_address_with_valid_input(self):
        """Valid address should return deliverable with high confidence."""
        adapter = MockUSPSAdapter()
        result = adapter.verify_address(
            USPSAddressInput(
                address_line1="123 Main St",
                address_line2="Apt 4",
                city="New York",
                state="NY",
                zip_code="10001"
            )
        )
        
        assert result.deliverable is True
        assert result.confidence == 0.9
        assert result.zip4 == "1234"
        assert result.zip5 == "10001"
        assert "123 Main St" in result.standardized_address
        assert "Apt 4" in result.standardized_address

    def test_verify_address_with_minimal_input(self):
        """Minimal valid input should still return deliverable."""
        adapter = MockUSPSAdapter()
        result = adapter.verify_address(
            USPSAddressInput(address_line1="456 Oak Ave")
        )
        
        assert result.deliverable is True
        assert result.confidence == 0.9
        assert result.zip4 == "1234"
        assert result.zip5 is None
        assert "456 Oak Ave" in result.standardized_address

    def test_verify_address_output_shape(self):
        """Result should have all expected fields."""
        adapter = MockUSPSAdapter()
        result = adapter.verify_address(
            USPSAddressInput(address_line1="789 Elm St", zip_code="90210")
        )
        
        # Check all fields exist
        assert hasattr(result, "deliverable")
        assert hasattr(result, "standardized_address")
        assert hasattr(result, "zip5")
        assert hasattr(result, "zip4")
        assert hasattr(result, "confidence")
        
        # Check types
        assert isinstance(result.deliverable, bool)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    def test_adapter_is_stateless(self):
        """Multiple calls should return consistent results (stateless)."""
        adapter = MockUSPSAdapter()
        input_data = USPSAddressInput(address_line1="100 Broadway")
        
        result1 = adapter.verify_address(input_data)
        result2 = adapter.verify_address(input_data)
        
        assert result1.deliverable == result2.deliverable
        assert result1.confidence == result2.confidence
        assert result1.zip4 == result2.zip4

    def test_verify_address_no_exceptions(self):
        """Should handle edge cases without raising exceptions."""
        adapter = MockUSPSAdapter()
        
        # Very long address
        long_address = "A" * 1000
        result = adapter.verify_address(
            USPSAddressInput(address_line1=long_address)
        )
        assert result.deliverable is True
        
        # Special characters
        special_address = "123 #$%^&() St"
        result = adapter.verify_address(
            USPSAddressInput(address_line1=special_address)
        )
        assert result.deliverable is True
