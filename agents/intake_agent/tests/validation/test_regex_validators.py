import datetime

import pytest

from utils.validation.regex_validators import (
    validate_ssn_last4,
    validate_email,
    validate_phone,
    validate_dob,
)


def test_validate_ssn_last4_none_is_valid():
    r = validate_ssn_last4(None)
    assert r.is_valid is True
    assert r.field == "ssn_last4"


def test_validate_ssn_last4_valid_and_invalid_cases():
    assert validate_ssn_last4("1234").is_valid is True

    r = validate_ssn_last4("12a4")
    assert r.is_valid is False
    assert "4 digits" in (r.reason or "")

    r = validate_ssn_last4("12345")
    assert r.is_valid is False
    assert "4 digits" in (r.reason or "")


def test_validate_email_cases():
    assert validate_email("user@example.com").is_valid is True

    r = validate_email("user@")
    assert r.is_valid is False
    assert "invalid email format" in (r.reason or "")

    r = validate_email("")
    assert r.is_valid is False
    assert "must not be empty" in (r.reason or "")


def test_validate_phone_cases():
    assert validate_phone("1234567890").is_valid is True
    assert validate_phone("+1-234-567-8901").is_valid is True

    r = validate_phone("1234")
    assert r.is_valid is False
    assert "10 to 15 digits" in (r.reason or "")


def test_validate_dob_today_and_future():
    today = datetime.date.today()
    assert validate_dob(today).is_valid is True

    future = today + datetime.timedelta(days=1)
    r = validate_dob(future)
    assert r.is_valid is False
    assert "cannot be in the future" in (r.reason or "")
