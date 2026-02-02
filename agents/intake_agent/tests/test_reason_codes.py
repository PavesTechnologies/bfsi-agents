from src.domain.validation.reason_codes import ValidationReasonCode


def test_reason_codes_are_defined():
    assert ValidationReasonCode.INVALID_FIRST_NAME.value == "INVALID_FIRST_NAME"
    assert ValidationReasonCode.INVALID_SSN_LAST4.value == "INVALID_SSN_LAST4"
    assert ValidationReasonCode.AGE_BELOW_MINIMUM.value == "AGE_BELOW_MINIMUM"
