"""
Mock PAN Verification Adapter (NSDL / UTIITSL).

Simulates:
  - PAN format validation ([A-Z]{5}[0-9]{4}[A-Z])
  - Name + DOB match against PAN records
  - PAN status: ACTIVE | INACTIVE | FLAGGED | INVALID_FORMAT
  - PAN–Aadhaar linkage check (mandatory per IT Act)

Scenario triggers:
  PAN first 5 chars == 'ZZZZZ' → PAN INACTIVE / FLAGGED
  Aadhaar prefix '8888'        → PAN–Aadhaar not linked
  Default                      → ACTIVE + linked
"""

import re
from typing import Any

from pydantic import BaseModel, field_validator

from src.workflows.kyc_engine.india_kyc_state import PANVerificationState

_PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


class PANRequest(BaseModel):
    pan_number: str
    full_name: str
    dob: str           # YYYY-MM-DD
    aadhaar_number: str

    @field_validator("pan_number")
    @classmethod
    def upper_pan(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("aadhaar_number")
    @classmethod
    def clean_aadhaar(cls, v: str) -> str:
        return re.sub(r"\s+", "", v)


class MockPANAdapter:
    """
    Mock PAN verification adapter.

    Scenario triggers:
      PAN first 5 chars == 'ZZZZZ' → INACTIVE / FLAGGED
      Aadhaar prefix '8888'        → PAN–Aadhaar not linked
      Default                      → ACTIVE + linked
    """

    def verify(self, raw_payload: dict[str, Any]) -> PANVerificationState:
        req = PANRequest(**raw_payload)
        flags: dict[str, str] = {}

        if not _PAN_REGEX.match(req.pan_number):
            return PANVerificationState(
                pan_verified=False,
                name_match=False,
                pan_status="INVALID_FORMAT",
                pan_aadhaar_linked=False,
                flags={"PAN_FORMAT_INVALID": f"PAN {req.pan_number!r} does not match required format [A-Z]{{5}}[0-9]{{4}}[A-Z]"},
            )

        if req.pan_number[:5] == "ZZZZZ":
            flags["PAN_INACTIVE"] = "PAN is marked INACTIVE or FLAGGED in NSDL records"
            return PANVerificationState(
                pan_verified=False,
                name_match=False,
                pan_status="INACTIVE",
                pan_aadhaar_linked=False,
                flags=flags,
            )

        aadhaar_prefix = req.aadhaar_number[:4] if len(req.aadhaar_number) >= 4 else ""
        pan_aadhaar_linked = aadhaar_prefix != "8888"
        if not pan_aadhaar_linked:
            flags["PAN_AADHAAR_NOT_LINKED"] = "PAN and Aadhaar are not linked as per Income Tax portal records"

        name_parts = req.full_name.upper().split()
        name_match = len(name_parts) >= 1 and len(name_parts[0]) >= 2

        return PANVerificationState(
            pan_verified=True,
            name_match=name_match,
            pan_status="ACTIVE",
            pan_aadhaar_linked=pan_aadhaar_linked,
            flags=flags,
        )
