"""
Mock AML / Sanctions / PEP screening adapter.

This is intentionally deterministic and driven off the SSN area number
and simple name patterns so that scenarios are easy to trigger in tests
and demos – similar in spirit to the other mock adapters.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.workflows.kyc_engine.kyc_state import AMLCheckState


class AMLRequestPayload(BaseModel):
    full_name: str
    dob: str  # ISO date string "YYYY-MM-DD"
    ssn: str = Field(..., min_length=9, max_length=9)
    address_line1: str
    city: str
    state: str
    zip: str

    @field_validator("ssn")
    @classmethod
    def clean_ssn(cls, v: str) -> str:
        return v.replace("-", "").strip()


class AMLScreeningResponse(BaseModel):
    """
    Normalized AML / sanctions screening output.
    This closely mirrors AMLCheckState so that the node
    can return it directly into the LangGraph state.
    """

    ofac_match: bool
    ofac_confidence: float
    pep_match: bool
    sanctions_list_version: str
    aml_score: float
    flags: dict[str, str]


class MockAMLAdapter:
    """
    Mock AML vendor.

    Uses simple, transparent rules based on SSN prefix and name patterns:
    - 900–909 → hard OFAC match
    - 910–919 → PEP match only
    - 920–929 → both OFAC + PEP
    - otherwise → clean profile with low AML score
    """

    DEFAULT_LIST_VERSION = "2026-01"

    def get_aml_screening(self, raw_payload: dict[str, Any]) -> AMLCheckState:
        req = AMLRequestPayload(**raw_payload)

        area_number = int(req.ssn[:3])
        full_name_upper = req.full_name.upper()

        # Baseline clean result
        ofac_match = False
        pep_match = False
        ofac_confidence = 0.0
        aml_score = 0.05
        flags: dict[str, str] = {}

        # ---------- Scenario 1: Explicit name-based OFAC demo ----------
        if "OFAC" in full_name_upper or "SANCTIONED" in full_name_upper:
            ofac_match = True
            ofac_confidence = 0.99
            aml_score = 0.99
            flags["OFAC_NAME_MATCH"] = "Name explicitly marked as sanctioned in mock data"

        # ---------- Scenario 2: SSN-driven scenarios ----------
        elif 900 <= area_number <= 909:
            # Hard OFAC hit
            ofac_match = True
            ofac_confidence = 0.97
            aml_score = 0.95
            flags["OFAC_AREA_RANGE"] = "SSN prefix mapped to OFAC list in mock rules"

        elif 910 <= area_number <= 919:
            # PEP only
            pep_match = True
            ofac_match = False
            ofac_confidence = 0.10
            aml_score = 0.70
            flags["PEP_AREA_RANGE"] = "SSN prefix mapped to PEP list in mock rules"

        elif 920 <= area_number <= 929:
            # Both OFAC + PEP – highest risk
            ofac_match = True
            pep_match = True
            ofac_confidence = 0.98
            aml_score = 0.99
            flags["OFAC_PEP_COMBINED"] = "SSN prefix mapped to combined OFAC+PEP scenario"

        # ---------- Default low‑risk profile ----------
        else:
            flags["CLEAN_PROFILE"] = "No OFAC / PEP match in mock rules"

        response = AMLScreeningResponse(
            ofac_match=ofac_match,
            ofac_confidence=ofac_confidence,
            pep_match=pep_match,
            sanctions_list_version=self.DEFAULT_LIST_VERSION,
            aml_score=aml_score,
            flags=flags,
        )

        # The LangGraph state expects AMLCheckState, which is structurally
        # compatible with this response model.
        return AMLCheckState(**response.model_dump())

