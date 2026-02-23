"""
Tests for address verification using Experian adapter.
Tests both the IdentityService method and the address_node directly.
"""

import pytest
from src.adapters.mock_adapters.mock_experian_adapter import MockExperianAdapter
from src.services.identity_service import IdentityService


# ── Fixtures ──────────────────────────────────────────────────────

GOLDEN_REQUEST = {
    "applicant_id": "user_9988",
    "full_name": "John Quincy Public",
    "dob": "1985-05-15",
    "ssn": "666451234",
    "address": {
        "line1": "1600 Pennsylvania Avenue NW",
        "city": "Washington",
        "state": "DC",
        "zip": "20500"
    },
    "phone": "+12024561111",
    "email": "jq.public@example.com"
}


def _get_experian_response(request):
    """Helper: call MockExperianAdapter for a given request."""
    adapter = MockExperianAdapter()
    return adapter.get_credit_report({
        "firstName": request["full_name"].split()[0],
        "lastName": request["full_name"].split()[-1],
        "street1": request["address"]["line1"],
        "city": request["address"]["city"],
        "state": request["address"]["state"],
        "zip": request["address"]["zip"],
        "ssn": request["ssn"]
    })


# ── IdentityService.process_address_verification ─────────────────

class TestAddressVerificationService:
    """Tests for IdentityService.process_address_verification"""

    def test_golden_path_address_match(self):
        """Matching address should produce address_match=True with low risk."""
        experian_data = _get_experian_response(GOLDEN_REQUEST)
        result = IdentityService.process_address_verification(GOLDEN_REQUEST, experian_data)

        assert result["address_match"] is True
        assert result["risk_score"] <= 0.25
        assert result["deliverable"] is True
        assert result["address_type"] == "Residential"
        assert result["standardized_address"] is not None
        assert len(result["standardized_address"]) > 0
        assert result["geo_risk_flag"] is False
        assert result["high_risk_country_flag"] is False
        print(f"  ✅ Golden path: match={result['address_match']}, risk={result['risk_score']}, flags={result['flags']}")

    def test_mismatched_city(self):
        """Different city should flag a mismatch."""
        request = {**GOLDEN_REQUEST, "address": {**GOLDEN_REQUEST["address"], "city": "New York"}}
        experian_data = _get_experian_response(GOLDEN_REQUEST)  # Use original for adapter
        result = IdentityService.process_address_verification(request, experian_data)

        assert "CITY_MISMATCH" in result["flags"]
        assert result["risk_score"] > 0.0
        print(f"  ✅ City mismatch: flags={result['flags']}, risk={result['risk_score']}")

    def test_mismatched_state(self):
        """Different state should flag a mismatch."""
        request = {**GOLDEN_REQUEST, "address": {**GOLDEN_REQUEST["address"], "state": "NY"}}
        experian_data = _get_experian_response(GOLDEN_REQUEST)
        result = IdentityService.process_address_verification(request, experian_data)

        assert "STATE_MISMATCH" in result["flags"]
        print(f"  ✅ State mismatch: flags={result['flags']}")

    def test_mismatched_zip(self):
        """Different zip should flag a mismatch."""
        request = {**GOLDEN_REQUEST, "address": {**GOLDEN_REQUEST["address"], "zip": "99999"}}
        experian_data = _get_experian_response(GOLDEN_REQUEST)
        result = IdentityService.process_address_verification(request, experian_data)

        assert "ZIP_MISMATCH" in result["flags"]
        print(f"  ✅ Zip mismatch: flags={result['flags']}")

    def test_completely_different_address_fails(self):
        """Completely different address should NOT match."""
        request = {**GOLDEN_REQUEST, "address": {
            "line1": "999 Ghost Lane",
            "city": "Nowhere",
            "state": "AK",
            "zip": "99999"
        }}
        experian_data = _get_experian_response(GOLDEN_REQUEST)
        result = IdentityService.process_address_verification(request, experian_data)

        assert result["address_match"] is False
        assert result["risk_score"] >= 0.75
        assert result["deliverable"] is False
        print(f"  ✅ Full mismatch: match={result['address_match']}, risk={result['risk_score']}, flags={result['flags']}")

    def test_standardized_address_populated(self):
        """Standardized address should come from Experian vendor data."""
        experian_data = _get_experian_response(GOLDEN_REQUEST)
        result = IdentityService.process_address_verification(GOLDEN_REQUEST, experian_data)

        std = result["standardized_address"]
        assert "line1" in std
        assert "city" in std
        assert "state" in std
        assert "zip" in std
        assert std["city"] != ""
        assert std["state"] != ""
        print(f"  ✅ Standardized: {std}")

    def test_all_required_state_keys_present(self):
        """Result should contain all keys defined in AddressVerificationState."""
        experian_data = _get_experian_response(GOLDEN_REQUEST)
        result = IdentityService.process_address_verification(GOLDEN_REQUEST, experian_data)

        required_keys = [
            "address_match", "risk_score", "geo_risk_flag",
            "high_risk_country_flag", "address_type", "usps_validated",
            "deliverable", "standardized_address", "flags"
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
        print(f"  ✅ All {len(required_keys)} required keys present")
