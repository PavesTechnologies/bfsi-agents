import pytest

@pytest.fixture
def perfect_match_fixture():
    """
    Triggers 'VALID PROFILE' branch (SSN Area 545-573).
    Validates PRD 6.1: Name-DOB-SSN consistency.
    """
    return {
        "firstName": "Jane",
        "lastName": "Doe",
        "full_name": "JANE DOE",
        "dob": "1980-04-15",
        "ssn": "545001234",
        "street1": "123 Main St",
        "city": "Phoenix",
        "state": "AZ",
        "zip": "85001"
    }

@pytest.fixture
def synthetic_fraud_fixture():
    """
    Triggers 'SYNTHETIC SSN' branch (SSN Area 600-619).
    Validates PRD 6.1: SSN issuance year correlation.
    The adapter will return an issuance year 5 years in the future.
    """
    return {
        "firstName": "Alex",
        "lastName": "Synth",
        "full_name": "ALEX SYNTH",
        "dob": "1995-05-20",
        "ssn": "605008888",
        "street1": "999 Ghost Lane",
        "city": "New York",
        "state": "NY",
        "zip": "10001"
    }

@pytest.fixture
def thin_file_fixture():
    """
    Triggers 'DEFAULT NORMAL' branch.
    Validates PRD 6.1 & 10.1: Identity with no specific fraud flags 
    but potentially low scores or limited history.
    """
    return {
        "firstName": "John",
        "lastName": "Newcomer",
        "full_name": "JOHN NEWCOMER",
        "dob": "2005-01-01",
        "ssn": "999001111",
        "street1": "456 Rookie Ave",
        "city": "Seattle",
        "state": "WA",
        "zip": "98101"
    }

@pytest.fixture
def deceased_person_fixture():
    """
    Triggers 'DECEASED SSN' branch (SSN Area 660-679).
    Validates PRD 8.2: Hard Fail signal for deceased records.
    """
    return {
        "firstName": "Robert",
        "lastName": "Legacy",
        "full_name": "ROBERT LEGACY",
        "dob": "1950-01-01",
        "ssn": "665000000",
        "street1": "1313 Cemetery Rd",
        "city": "Salem",
        "state": "MA",
        "zip": "01970"
    }