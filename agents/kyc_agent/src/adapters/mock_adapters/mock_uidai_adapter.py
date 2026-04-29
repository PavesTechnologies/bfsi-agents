"""
Mock UIDAI eKYC Adapter (Aadhaar verification).

Simulates the two-step OTP flow used by UIDAI:
  Step 1 – generate_otp: always returns OTP_SENT (or NOT_FOUND for prefix 9000)
  Step 2 – verify_otp:   returns full eKYC fields based on Aadhaar prefix

Scenario triggers (first 4 digits of Aadhaar):
  9000 → Aadhaar not found in UIDAI database
  4444 → OTP expired / invalid
  Default → SUCCESS with mocked identity fields
"""

import re
import uuid
from typing import Any

from pydantic import BaseModel, field_validator

from src.workflows.kyc_engine.india_kyc_state import AadhaarVerificationState

# Minimal 1×1 transparent PNG – used as placeholder face photo
_MOCK_PHOTO_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


class UIDAIRequest(BaseModel):
    aadhaar_number: str
    otp: str | None = None
    txn_id: str | None = None
    full_name: str
    dob: str  # YYYY-MM-DD

    @field_validator("aadhaar_number")
    @classmethod
    def clean_aadhaar(cls, v: str) -> str:
        clean = re.sub(r"\s+", "", v)
        if not clean.isdigit() or len(clean) != 12:
            raise ValueError("Aadhaar must be 12 digits")
        return clean


class MockUIDAIAdapter:
    """
    Mock UIDAI eKYC adapter.

    Scenario triggers (first 4 digits of Aadhaar):
      9000 → NOT_FOUND
      4444 → OTP_EXPIRED
      Default → SUCCESS
    """

    def generate_otp(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        req = UIDAIRequest(**raw_payload)
        prefix = req.aadhaar_number[:4]

        if prefix == "9000":
            return {
                "status": "NOT_FOUND",
                "txn_id": None,
                "message": "Aadhaar number not found in UIDAI database",
            }

        return {
            "status": "OTP_SENT",
            "txn_id": str(uuid.uuid4()),
            "message": "OTP sent to Aadhaar-linked mobile number",
        }

    def verify_otp(self, raw_payload: dict[str, Any]) -> AadhaarVerificationState:
        req = UIDAIRequest(**raw_payload)
        prefix = req.aadhaar_number[:4]
        masked = "XXXX-XXXX-" + req.aadhaar_number[-4:]

        if prefix == "9000":
            return AadhaarVerificationState(
                aadhaar_verified=False,
                name_match=False,
                dob_match=False,
                masked_aadhaar=masked,
                address_from_aadhaar={},
                photo_base64="",
                otp_status="NOT_FOUND",
                flags={"AADHAAR_NOT_FOUND": "Aadhaar number not present in UIDAI database"},
            )

        if prefix == "4444":
            return AadhaarVerificationState(
                aadhaar_verified=False,
                name_match=False,
                dob_match=False,
                masked_aadhaar=masked,
                address_from_aadhaar={},
                photo_base64="",
                otp_status="OTP_EXPIRED",
                flags={"OTP_EXPIRED": "OTP has expired or is invalid; request a new OTP"},
            )

        # Default: success – name/DOB match via simple non-empty check
        name_match = bool(req.full_name and len(req.full_name.strip()) > 3)
        dob_match = bool(req.dob and len(req.dob) == 10)

        return AadhaarVerificationState(
            aadhaar_verified=True,
            name_match=name_match,
            dob_match=dob_match,
            masked_aadhaar=masked,
            address_from_aadhaar={
                "line1": "12, MG Road",
                "line2": "Indiranagar",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
            },
            photo_base64=_MOCK_PHOTO_B64,
            otp_status="OTP_VERIFIED",
            flags={},
        )
