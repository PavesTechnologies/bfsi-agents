from src.domain.validation.typed_field_validators import validate_ssn_last4
from src.domain.validation.reason_codes import ValidationReasonCode


def test_invalid_ssn_last4_maps_to_reason_code():
    result = validate_ssn_last4("12A")

    assert result.passed is False
    assert result.reason_code == ValidationReasonCode.INVALID_SSN_LAST4
from datetime import date, timedelta
from src.domain.validation.typed_field_validators import validate_dob
from src.domain.validation.reason_codes import ValidationReasonCode


def test_underage_maps_to_age_below_minimum():
    dob = date.today() - timedelta(days=365 * 10)

    result = validate_dob(dob)

    assert result.passed is False
    assert result.reason_code == ValidationReasonCode.AGE_BELOW_MINIMUM
def test_validator_returns_single_reason_code():
    result = validate_ssn_last4("abc")

    assert result.reason_code is not None
    assert isinstance(result.reason_code, ValidationReasonCode)
