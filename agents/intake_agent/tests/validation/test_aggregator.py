import datetime

from utils.validation.aggregator import validate_applicant
from utils.validation.results import ValidationResult


class DummyApplicant:
    def __init__(self, email=None, ssn_last4=None, date_of_birth=None):
        self.email = email
        self.ssn_last4 = ssn_last4
        self.date_of_birth = date_of_birth


def test_aggregator_all_valid():
    today = datetime.date.today()
    dob = today.replace(year=today.year - 30)
    applicant = DummyApplicant(email="user@example.com", ssn_last4="1234", date_of_birth=dob)

    summary = validate_applicant(applicant)
    assert summary.is_valid is True
    assert summary.failed_fields == []
    assert all(isinstance(r, ValidationResult) for r in summary.results)


def test_aggregator_invalid_email():
    today = datetime.date.today()
    dob = today.replace(year=today.year - 30)
    applicant = DummyApplicant(email="bad@", ssn_last4="1234", date_of_birth=dob)

    summary = validate_applicant(applicant)
    assert summary.is_valid is False
    assert "email" in summary.failed_fields


def test_aggregator_multiple_failures():
    today = datetime.date.today()
    dob_under = today.replace(year=today.year - 17)
    applicant = DummyApplicant(email="bad@", ssn_last4="12a4", date_of_birth=dob_under)

    summary = validate_applicant(applicant)
    assert summary.is_valid is False
    # both validators related to date_of_birth may fail but failed_fields should be unique
    assert set(summary.failed_fields) == {"email", "ssn_last4", "date_of_birth"}


def test_aggregator_never_raises_for_unexpected_input():
    # Passing an object missing attributes should not raise and should return a summary
    class Minimal:
        pass

    summary = validate_applicant(Minimal())
    assert isinstance(summary.is_valid, bool)
    assert isinstance(summary.results, list)
    # Should contain ValidationResult objects describing failures
    assert any(not r.is_valid for r in summary.results)
