"""
Mock AML / Sanctions screening adapter for India.

Checks against:
  - RBI sanctions list
  - UNSC (UN Security Council) consolidated list
  - PEP (Politically Exposed Persons) registry

Scenario triggers:
  Aadhaar prefix '7777'       → RBI sanctions hit
  Name contains 'RBI_BLOCK'   → RBI sanctions hit (explicit demo marker)
  Name contains 'UNSC_LIST'   → UNSC watchlist hit
  Name contains 'PEP_MATCH'   → PEP match
  Default                     → clean profile (aml_score 0.02)
"""

import re
from typing import Any

from pydantic import BaseModel, field_validator

from src.workflows.kyc_engine.india_kyc_state import AMLIndiaState


class AMLIndiaRequest(BaseModel):
    full_name: str
    dob: str
    aadhaar_number: str
    pan_number: str

    @field_validator("aadhaar_number")
    @classmethod
    def strip_spaces(cls, v: str) -> str:
        return re.sub(r"\s+", "", v)


class MockAMLIndiaAdapter:
    """
    Mock Indian AML watchlist screening adapter.

    Scenario triggers:
      Aadhaar prefix '7777'       → RBI sanctions match
      'RBI_BLOCK' in name         → RBI sanctions match
      'UNSC_LIST' in name         → UNSC match
      'PEP_MATCH' in name         → PEP match
      Default                     → clean (aml_score 0.02)
    """

    WATCHLIST_VERSION = "RBI-UNSC-2026-Q1"

    def screen(self, raw_payload: dict[str, Any]) -> AMLIndiaState:
        req = AMLIndiaRequest(**raw_payload)
        name_upper = req.full_name.upper()
        aadhaar_prefix = req.aadhaar_number[:4] if len(req.aadhaar_number) >= 4 else ""

        rbi_match = False
        unsc_match = False
        pep_match = False
        aml_score = 0.02
        flags: dict[str, str] = {}

        if "RBI_BLOCK" in name_upper:
            rbi_match = True
            aml_score = 0.97
            flags["RBI_SANCTIONS_HIT"] = "Name found in RBI sanctions list (mock: RBI_BLOCK keyword)"

        if "UNSC_LIST" in name_upper:
            unsc_match = True
            aml_score = max(aml_score, 0.99)
            flags["UNSC_HIT"] = "Name found in UNSC consolidated watchlist (mock: UNSC_LIST keyword)"

        if "PEP_MATCH" in name_upper:
            pep_match = True
            aml_score = max(aml_score, 0.75)
            flags["PEP_HIT"] = "Name matched against PEP registry (mock: PEP_MATCH keyword)"

        if aadhaar_prefix == "7777" and not rbi_match:
            rbi_match = True
            aml_score = max(aml_score, 0.96)
            flags["RBI_SANCTIONS_PREFIX"] = "Aadhaar prefix 7777 mapped to RBI sanctions scenario in mock rules"

        if not flags:
            flags["CLEAN_PROFILE"] = "No match found on RBI / UNSC / PEP watchlists"

        return AMLIndiaState(
            rbi_match=rbi_match,
            unsc_match=unsc_match,
            pep_match=pep_match,
            aml_score=aml_score,
            watchlist_version=self.WATCHLIST_VERSION,
            flags=flags,
        )
