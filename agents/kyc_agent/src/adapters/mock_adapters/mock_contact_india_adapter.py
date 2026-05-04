"""
Mock Contact Verification Adapter for India.

Validates Indian mobile number (+91, 10-digit, TRAI compliant).

Scenario triggers:
  Phone '9999999999' → VOIP / virtual carrier
  Phone '8888888888' → high-risk SIM
  Default            → valid phone
"""

import re
from typing import Any

from src.workflows.kyc_engine.india_kyc_state import ContactIndiaState

_VOIP_NUMBERS = {"9999999999"}
_HIGH_RISK_NUMBERS = {"8888888888"}


class MockContactIndiaAdapter:

    def verify(self, raw_payload: dict[str, Any]) -> ContactIndiaState:
        phone: str = raw_payload.get("phone", "")
        flags: dict[str, str] = {}

        clean_phone = re.sub(r"[\s\-\(\)]", "", phone)
        if clean_phone.startswith("+91"):
            clean_phone = clean_phone[3:]
        elif clean_phone.startswith("91") and len(clean_phone) == 12:
            clean_phone = clean_phone[2:]
        elif clean_phone.startswith("0"):
            clean_phone = clean_phone[1:]

        phone_valid = clean_phone.isdigit() and len(clean_phone) == 10
        is_voip = clean_phone in _VOIP_NUMBERS
        is_high_risk = clean_phone in _HIGH_RISK_NUMBERS

        if not phone_valid:
            flags["PHONE_INVALID"] = f"Phone {phone!r} is not a valid 10-digit Indian mobile number"
        if is_voip:
            flags["VOIP_DETECTED"] = "Phone number is linked to a VOIP / virtual carrier"
        if is_high_risk:
            flags["HIGH_RISK_SIM"] = "Phone number is flagged as high-risk in telecom database"

        formatted_phone = f"+91{clean_phone}" if phone_valid else phone

        return ContactIndiaState(
            phone_valid=phone_valid and not is_voip,
            is_voip=is_voip,
            is_high_risk=is_high_risk,
            formatted_phone=formatted_phone,
            flags=flags,
        )
