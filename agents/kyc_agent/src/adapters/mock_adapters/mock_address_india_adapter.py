"""
Mock Indian Address Verification Adapter.

Validates:
  - Pincode (6-digit, mapped to known state/district)
  - Address content (hard-fail keywords: GHOST, INVALID, UNKNOWN, FAKE, TEST_FAIL)
  - Returns standardised address with resolved state and district

Scenario triggers:
  'GHOST' / 'INVALID' / 'UNKNOWN' / 'FAKE' / 'TEST_FAIL' in line1 → address_valid: False
  Unknown pincode → pincode_valid: False (address still accepted with soft flag)
  Default → valid, standardised
"""

from typing import Any

from src.workflows.kyc_engine.india_kyc_state import AddressIndiaState

# Subset of pincode → (state, district) for major cities
_PINCODE_MAP: dict[str, tuple[str, str]] = {
    "110001": ("Delhi", "Central Delhi"),
    "110002": ("Delhi", "Central Delhi"),
    "110003": ("Delhi", "South Delhi"),
    "400001": ("Maharashtra", "Mumbai City"),
    "400002": ("Maharashtra", "Mumbai City"),
    "400050": ("Maharashtra", "Mumbai Suburban"),
    "560001": ("Karnataka", "Bengaluru Urban"),
    "560002": ("Karnataka", "Bengaluru Urban"),
    "560100": ("Karnataka", "Bengaluru Rural"),
    "600001": ("Tamil Nadu", "Chennai"),
    "600002": ("Tamil Nadu", "Chennai"),
    "500001": ("Telangana", "Hyderabad"),
    "500002": ("Telangana", "Hyderabad"),
    "700001": ("West Bengal", "Kolkata"),
    "700002": ("West Bengal", "Kolkata"),
    "411001": ("Maharashtra", "Pune"),
    "411002": ("Maharashtra", "Pune"),
    "302001": ("Rajasthan", "Jaipur"),
    "380001": ("Gujarat", "Ahmedabad"),
    "226001": ("Uttar Pradesh", "Lucknow"),
    "462001": ("Madhya Pradesh", "Bhopal"),
    "492001": ("Chhattisgarh", "Raipur"),
    "682001": ("Kerala", "Ernakulam"),
    "500034": ("Telangana", "Hyderabad"),
}

_HARD_FAIL_KEYWORDS = {"GHOST", "INVALID", "UNKNOWN", "FAKE", "TEST_FAIL"}


class MockAddressIndiaAdapter:
    """
    Mock Indian address verification adapter.

    Scenario triggers:
      Hard-fail keywords in line1 → address_valid: False (hard stop)
      Unknown pincode             → pincode_valid: False, soft flag only
      Default                     → valid + standardised
    """

    def verify(self, raw_payload: dict[str, Any]) -> AddressIndiaState:
        line1: str = raw_payload.get("line1", "").upper()
        line2: str = raw_payload.get("line2", "")
        city: str = raw_payload.get("city", "")
        state_in: str = raw_payload.get("state", "")
        pincode: str = str(raw_payload.get("pincode", "")).strip()
        flags: dict[str, str] = {}

        if any(kw in line1 for kw in _HARD_FAIL_KEYWORDS):
            flags["ADDRESS_INVALID"] = f"Address contains invalid keyword in line1: {line1!r}"
            return AddressIndiaState(
                address_valid=False,
                pincode_valid=False,
                state="",
                district="",
                standardized_address={},
                flags=flags,
            )

        pincode_entry = _PINCODE_MAP.get(pincode)
        pincode_valid = pincode_entry is not None
        resolved_state = pincode_entry[0] if pincode_entry else state_in
        resolved_district = pincode_entry[1] if pincode_entry else city

        if not pincode_valid:
            flags["PINCODE_UNKNOWN"] = f"Pincode {pincode!r} not in reference data; address accepted with manual review recommended"

        standardized = {
            "line1": raw_payload.get("line1", "").strip(),
            "line2": line2.strip(),
            "city": resolved_district or city,
            "state": resolved_state,
            "pincode": pincode,
            "country": "India",
        }

        return AddressIndiaState(
            address_valid=True,
            pincode_valid=pincode_valid,
            state=resolved_state,
            district=resolved_district or city,
            standardized_address=standardized,
            flags=flags,
        )
