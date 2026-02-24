from src.adapters.mock_adapters.mock_experian_adapter import MockExperianAdapter
from src.services.identity_service import IdentityService


def test_leap_year_dob_processing(leap_year_dob_fixture):
    """Ensures age calculation is accurate for February 29th births."""
    adapter = MockExperianAdapter()
    vendor_response = adapter.get_credit_report(leap_year_dob_fixture)
    print(
        f"Vendor Response DOB: {vendor_response.consumerIdentity.dob}"
    )  # Debug log for vendor DOB parsing

    state = IdentityService.process_ssn_verification(
        leap_year_dob_fixture, vendor_response
    )

    # 1996-02-29 is a valid date; ensure ssn_valid is True per age sanity rules
    assert state["ssn_valid"] is True
    assert state["dob_ssn_match"] is True


def test_max_length_resilience(max_length_identity_fixture):
    """Validates that the adapter and Pydantic models handle long strings."""
    adapter = MockExperianAdapter()
    # This triggers Pydantic validation in ExperianRequestPayload
    vendor_response = adapter.get_credit_report(max_length_identity_fixture)

    assert (
        vendor_response.consumerIdentity.name[0].firstName
        == max_length_identity_fixture["firstName"].upper()
    )


def test_special_character_normalization(special_char_address_fixture):
    """Ensures special characters like apostrophes don't break string splitting."""
    adapter = MockExperianAdapter()
    vendor_response = adapter.get_credit_report(special_char_address_fixture)

    # Verify street number extraction for non-standard "12-34 1/2" format
    # Your adapter currently uses .split(" ", 1)
    addr = vendor_response.addressInformation[0]
    assert addr.streetNumber == "12-34"
