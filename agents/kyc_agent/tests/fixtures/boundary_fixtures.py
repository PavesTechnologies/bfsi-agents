import pytest


@pytest.fixture
def leap_year_dob_fixture():
    """Validates date parsing for February 29th (Leap Year)."""
    return {
        "firstName": "LEAP",
        "lastName": "YEAR",
        "full_name": "LEAP YEAR",
        "dob": "1996-02-29",  # Valid leap year
        "ssn": "546002929",
        "street1": "29 LEAP ST",
        "city": "DATETOWN",
        "state": "CA",
        "zip": "90210",
    }


@pytest.fixture
def max_length_identity_fixture():
    """Tests system stability with extremely long name and address strings."""
    return {
        "firstName": "EXTREMELYLONGFIRSTNAMETHATIGHTCAUSESCHEMAISSUES",
        "lastName": "VON-STRATTON-UPPER-MIDDLE-CLAN-THE-THIRD-ESQUIRE",
        "full_name": "EXTREMELYLONGFIRSTNAMETHATIGHTCAUSESCHEMAISSUES VON-STRATTON-UPPER-MIDDLE-CLAN-THE-THIRD-ESQUIRE",  # noqa: E501
        "dob": "1985-06-15",
        "ssn": "545009999",
        "street1": "1234567890 BOURBON STREET NORTHWEST SUITE 1000 OFFICE B FLOOR 42",
        "city": "SAN FRANCISCO BAY AREA METROPOLITAN DISTRICT",
        "state": "CA",
        "zip": "94105",
    }


@pytest.fixture
def special_char_address_fixture():
    """Tests handling of non-standard address formats and special characters."""
    return {
        "firstName": "Rénée",
        "lastName": "O'Malley-Smith",
        "full_name": "Rénée O'Malley-Smith",
        "dob": "1990-11-11",
        "ssn": "545007777",
        "street1": "12-34 1/2 81st St. #4B",
        "city": "St. Louis",
        "state": "MO",
        "zip": "63101",
    }
