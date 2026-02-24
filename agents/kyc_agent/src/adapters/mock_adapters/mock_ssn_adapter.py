from typing import Any


class MockSSNAdapter:
    """
    Mock for SSN Identity Trace.
    Retrieves the full identity record associated with the SSN prefix.
    """

    def get_ssn_details(self, ssn: str) -> dict[str, Any]:
        clean_ssn = ssn.replace("-", "").strip()

        # Validation for the adapter itself (PRD Section 5.1)
        if not clean_ssn.isdigit() or len(clean_ssn) != 9:
            return {"ssn_valid": False, "error": "Invalid SSN format"}

        area_number = int(clean_ssn[:3])

        # Scenario: Simulated Synthetic/High Risk (NY Area)
        if area_number == 0:
            return {
                "ssn_valid": True,
                "first_name": "Robert",
                "last_name": "Mismatched",
                "dob": "1975-01-01",
                "address": "1001 MONTOR RD, STREW LONE, NY 10001",
                "issued_state": "NY",
                "ssn_issue_date": "1951-06-15",
                "issuance_range": "1950-1952",
                "name_match_score": 0.10,
                "deceased_flag": False,
                "synthetic_fraud_indicator": "HIGH",
            }

        # Scenario: West Coast / California Prefix
        if 545 <= area_number <= 573:
            return {
                "ssn_valid": True,
                "first_name": "Jane",
                "last_name": "Doe",
                "dob": "1991-03-22",
                "address": "456 Sunset Blvd, Los Angeles, CA 90028",
                "issued_state": "CA",
                "ssn_issue_date": "1991-08-10",
                "issuance_range": "1990-1992",
                "name_match_score": 0.95,
                "deceased_flag": False,
                "synthetic_fraud_indicator": "LOW",
            }

        # Scenario: East Coast / DC (Matches Golden Path Document Data)
        if 574 <= area_number <= 576:
            return {
                "ssn_valid": True,
                "first_name": "John",
                "last_name": "Public",
                "dob": "1985-05-15",
                "address": "1600 Pennsylvania Avenue NW, Washington, DC 20500",
                "issued_state": "DC",
                "ssn_issue_date": "1985-11-20",
                "issuance_range": "1984-1986",
                "name_match_score": 0.98,
                "deceased_flag": False,
                "synthetic_fraud_indicator": "LOW",
            }

        # Default Fallback (Randomization Era)
        return {
            "ssn_valid": True,
            "first_name": "Generic",
            "last_name": "User",
            "dob": "2012-10-10",
            "address": "123 Main St, Springfield, IL 62704",
            "issued_state": "Unknown",
            "ssn_issue_date": "2012-12-01",
            "issuance_range": "2011-Present",
            "name_match_score": 0.50,
            "deceased_flag": False,
            "synthetic_fraud_indicator": "MEDIUM",
        }
