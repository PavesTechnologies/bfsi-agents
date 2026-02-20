"""
AML Screening Node

Second stage of KYC compliance pipeline.
Screens applicant against sanctions lists and AML watchlists.
"""

from src.workflows.kyc_engine.kyc_state import (
    KYCState,
    AMLResult,
    EventType,
    KYCStatus,
)


def run_aml(state: KYCState) -> KYCState:
    """Perform AML screening (OFAC + PEP)."""

    state.add_history_entry(EventType.AML_STARTED, "aml_screening")
    state.current_stage = "aml_screening"

    try:
        if state.identity is None:
            raise ValueError("Identity must complete before AML screening")

        # -------------------------
        # MOCK SCREENING RESULTS
        # -------------------------
        ofac_match = False
        pep_match = False
        matches_found = 0

        # (Future: replace with vendor integration)
        # Example deterministic behavior:
        name = state.applicant_data.get("full_name", "").lower()

        if "terror" in name:
            ofac_match = True
            matches_found = 1

        if "minister" in name:
            pep_match = True
            matches_found += 1

        # Save result
        state.aml = AMLResult(
            matches_found=matches_found,
            match_details=[],
            sources_checked=["OFAC", "PEP"],
            ofac_match=ofac_match,
            pep_match=pep_match,
        )

        # -------------------------
        # HARD FAIL (OFAC)
        # -------------------------
        if ofac_match:
            state.hard_fail_triggered = True
            state.flags.append("OFAC_MATCH")
            state.status = KYCStatus.FAILED

        # -------------------------
        # REVIEW FLAG (PEP)
        # -------------------------
        if pep_match:
            state.flags.append("PEP_MATCH")

        state.add_history_entry(
            EventType.AML_COMPLETE,
            "aml_screening",
            {"ofac": ofac_match, "pep": pep_match},
        )

    except Exception as e:
        state.error = str(e)
        state.status = KYCStatus.FAILED
        state.add_history_entry(EventType.AML_FAILED, "aml_screening", error=str(e))

    return state
