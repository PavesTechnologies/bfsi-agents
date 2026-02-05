"""Tests for mock email adapter."""
import pytest
from src.adapters.http.email_risk.interfaces import EmailInput
from src.adapters.http.email_risk.mock_adapter import MockEmailAdapter


class TestMockEmailAdapter:
    """Test suite for MockEmailAdapter."""

    def test_analyze_gmail_domain(self):
        """Gmail should be marked as low risk."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="user@gmail.com")
        )
        
        assert result.domain == "gmail.com"
        assert result.risk == "low"
        assert result.disposable is False
        assert result.confidence == 0.95

    def test_analyze_outlook_domain(self):
        """Outlook should be marked as low risk."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="user@outlook.com")
        )
        
        assert result.domain == "outlook.com"
        assert result.risk == "low"
        assert result.disposable is False
        assert result.confidence == 0.95

    def test_analyze_yahoo_domain(self):
        """Yahoo should be marked as low risk."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="user@yahoo.com")
        )
        
        assert result.domain == "yahoo.com"
        assert result.risk == "low"
        assert result.disposable is False

    def test_analyze_icloud_domain(self):
        """iCloud should be marked as low risk."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="user@icloud.com")
        )
        
        assert result.domain == "icloud.com"
        assert result.risk == "low"
        assert result.disposable is False

    def test_analyze_mailinator_domain(self):
        """Mailinator should be marked as high risk and disposable."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="user@mailinator.com")
        )
        
        assert result.domain == "mailinator.com"
        assert result.risk == "high"
        assert result.disposable is True
        assert result.confidence == 0.98

    def test_analyze_tempmail_domain(self):
        """Tempmail should be marked as high risk and disposable."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="user@tempmail.com")
        )
        
        assert result.domain == "tempmail.com"
        assert result.risk == "high"
        assert result.disposable is True

    def test_analyze_guerrillamail_domain(self):
        """Guerrillamail should be marked as high risk and disposable."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="user@guerrillamail.com")
        )
        
        assert result.domain == "guerrillamail.com"
        assert result.risk == "high"
        assert result.disposable is True

    def test_analyze_company_domain(self):
        """Company domains should be marked as medium risk."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="user@company.com")
        )
        
        assert result.domain == "company.com"
        assert result.risk == "medium"
        assert result.disposable is False
        assert result.confidence == 0.80

    def test_analyze_unknown_domain(self):
        """Unknown domains should be marked as medium risk."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="user@example.org")
        )
        
        assert result.domain == "example.org"
        assert result.risk == "medium"
        assert result.disposable is False

    def test_analyze_email_case_insensitive(self):
        """Domain extraction should be case-insensitive."""
        adapter = MockEmailAdapter()
        
        result_upper = adapter.analyze_email_domain(
            EmailInput(email="user@GMAIL.COM")
        )
        result_mixed = adapter.analyze_email_domain(
            EmailInput(email="user@Gmail.Com")
        )
        
        assert result_upper.domain == "gmail.com"
        assert result_mixed.domain == "gmail.com"
        assert result_upper.risk == "low"
        assert result_mixed.risk == "low"

    def test_analyze_email_with_subdomain(self):
        """Should extract full domain including subdomains."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="user@mail.example.com")
        )
        
        assert result.domain == "mail.example.com"
        assert result.risk == "medium"

    def test_analyze_email_with_empty_string(self):
        """Empty email should be invalid."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="")
        )
        
        assert result.domain == ""
        assert result.risk == "high"
        assert result.disposable is True
        assert result.confidence == 0.0

    def test_analyze_email_without_at_sign(self):
        """Email without @ should be invalid."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="notanemail")
        )
        
        assert result.domain == ""
        assert result.risk == "high"
        assert result.disposable is True

    def test_analyze_email_with_multiple_at_signs(self):
        """Should extract domain after first @ sign."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="user+tag@gmail.com@other.com")
        )
        
        assert result.domain == "gmail.com"
        assert result.risk == "low"

    def test_analyze_email_output_shape(self):
        """Result should have all expected fields."""
        adapter = MockEmailAdapter()
        result = adapter.analyze_email_domain(
            EmailInput(email="test@example.com")
        )
        
        # Check all fields exist
        assert hasattr(result, "domain")
        assert hasattr(result, "risk")
        assert hasattr(result, "disposable")
        assert hasattr(result, "confidence")
        
        # Check types
        assert isinstance(result.domain, str)
        assert isinstance(result.disposable, bool)
        assert isinstance(result.confidence, float)
        assert result.risk in ["low", "medium", "high"]
        assert 0.0 <= result.confidence <= 1.0

    def test_adapter_is_stateless(self):
        """Multiple calls should return consistent results."""
        adapter = MockEmailAdapter()
        input_data = EmailInput(email="user@mailinator.com")
        
        result1 = adapter.analyze_email_domain(input_data)
        result2 = adapter.analyze_email_domain(input_data)
        
        assert result1.domain == result2.domain
        assert result1.risk == result2.risk
        assert result1.disposable == result2.disposable
        assert result1.confidence == result2.confidence

    def test_analyze_email_no_exceptions(self):
        """Should handle edge cases without raising exceptions."""
        adapter = MockEmailAdapter()
        
        # Very long email
        long_email = "a" * 1000 + "@company.com"
        result = adapter.analyze_email_domain(
            EmailInput(email=long_email)
        )
        assert result.risk == "medium"
        
        # Special characters
        special_email = "user+tag!#$@example.com"
        result = adapter.analyze_email_domain(
            EmailInput(email=special_email)
        )
        assert result.domain == "example.com"
        assert result.risk == "medium"
