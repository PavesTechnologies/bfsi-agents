"""Tests for mock employer adapter."""
import pytest
from src.adapters.http.employer.interfaces import EmployerInput
from src.adapters.http.employer.mock_adapter import MockEmployerAdapter


class TestMockEmployerAdapter:
    """Test suite for MockEmployerAdapter."""

    def test_verify_employer_with_inc_keyword(self):
        """Employer name with 'inc' should be verified."""
        adapter = MockEmployerAdapter()
        result = adapter.verify_employer(
            EmployerInput(employer_name="Acme Inc")
        )
        
        assert result.verified is True
        assert result.confidence == 0.85
        assert result.naics_code == "541512"
        assert result.normalized_name == "Acme Inc"

    def test_verify_employer_with_corp_keyword(self):
        """Employer name with 'corp' should be verified."""
        adapter = MockEmployerAdapter()
        result = adapter.verify_employer(
            EmployerInput(employer_name="Tech Corp")
        )
        
        assert result.verified is True
        assert result.naics_code == "541512"

    def test_verify_employer_with_llc_keyword(self):
        """Employer name with 'llc' should be verified."""
        adapter = MockEmployerAdapter()
        result = adapter.verify_employer(
            EmployerInput(employer_name="Startup LLC")
        )
        
        assert result.verified is True
        assert result.naics_code == "541512"

    def test_verify_employer_case_insensitive(self):
        """Keywords should be matched case-insensitively."""
        adapter = MockEmployerAdapter()
        
        result_upper = adapter.verify_employer(
            EmployerInput(employer_name="Company INC")
        )
        result_lower = adapter.verify_employer(
            EmployerInput(employer_name="company inc")
        )
        result_mixed = adapter.verify_employer(
            EmployerInput(employer_name="Company Inc")
        )
        
        assert result_upper.verified is True
        assert result_lower.verified is True
        assert result_mixed.verified is True

    def test_verify_employer_without_corporate_keyword(self):
        """Employer without corporate keywords should not be verified."""
        adapter = MockEmployerAdapter()
        result = adapter.verify_employer(
            EmployerInput(employer_name="Joe's Pizza")
        )
        
        assert result.verified is False
        assert result.confidence == 0.0
        assert result.naics_code is None
        assert result.normalized_name == "Joe's Pizza"

    def test_verify_employer_with_empty_name(self):
        """Empty employer name should not be verified."""
        adapter = MockEmployerAdapter()
        result = adapter.verify_employer(
            EmployerInput(employer_name="")
        )
        
        assert result.verified is False
        assert result.confidence == 0.0
        assert result.naics_code is None

    def test_verify_employer_with_whitespace_only(self):
        """Whitespace-only employer name should not be verified."""
        adapter = MockEmployerAdapter()
        result = adapter.verify_employer(
            EmployerInput(employer_name="   ")
        )
        
        assert result.verified is False
        assert result.confidence == 0.0

    def test_verify_employer_with_all_optional_fields(self):
        """Should handle all optional fields without error."""
        adapter = MockEmployerAdapter()
        result = adapter.verify_employer(
            EmployerInput(
                employer_name="Global Solutions Corp",
                employer_phone="+1-555-0100",
                employer_address="123 Business Ave"
            )
        )
        
        assert result.verified is True
        assert result.naics_code == "541512"

    def test_verify_employer_output_shape(self):
        """Result should have all expected fields."""
        adapter = MockEmployerAdapter()
        result = adapter.verify_employer(
            EmployerInput(employer_name="Test Ltd")
        )
        
        # Check all fields exist
        assert hasattr(result, "verified")
        assert hasattr(result, "normalized_name")
        assert hasattr(result, "naics_code")
        assert hasattr(result, "confidence")
        
        # Check types
        assert isinstance(result.verified, bool)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    def test_adapter_is_stateless(self):
        """Multiple calls should return consistent results."""
        adapter = MockEmployerAdapter()
        input_data = EmployerInput(employer_name="Persistent Inc")
        
        result1 = adapter.verify_employer(input_data)
        result2 = adapter.verify_employer(input_data)
        
        assert result1.verified == result2.verified
        assert result1.confidence == result2.confidence
        assert result1.naics_code == result2.naics_code

    def test_verify_employer_keyword_in_middle(self):
        """Keywords anywhere in the name should match."""
        adapter = MockEmployerAdapter()
        
        # Keyword at beginning
        result_begin = adapter.verify_employer(
            EmployerInput(employer_name="Inc Solutions")
        )
        # Keyword at end
        result_end = adapter.verify_employer(
            EmployerInput(employer_name="Solutions Inc")
        )
        # Keyword in middle
        result_middle = adapter.verify_employer(
            EmployerInput(employer_name="Best Inc Solutions")
        )
        
        assert result_begin.verified is True
        assert result_end.verified is True
        assert result_middle.verified is True

    def test_verify_employer_no_exceptions(self):
        """Should handle edge cases without raising exceptions."""
        adapter = MockEmployerAdapter()
        
        # Very long name
        long_name = "A" * 1000 + " Corp"
        result = adapter.verify_employer(
            EmployerInput(employer_name=long_name)
        )
        assert result.verified is True
        
        # Special characters
        special_name = "Company #123 LLC"
        result = adapter.verify_employer(
            EmployerInput(employer_name=special_name)
        )
        assert result.verified is True
