"""
Identity Verification Node

First stage of KYC compliance pipeline.
Verifies applicant identity against authoritative sources.
"""

from src.workflows.kyc_engine.kyc_state import (
    KYCState,
    IdentityResult,
    EventType,
    KYCStatus,
)


def run_identity(state: KYCState) -> KYCState:
    """Perform identity verification step."""

    state.add_history_entry(EventType.IDENTITY_STARTED, "identity_verification")
    state.current_stage = "identity_verification"

    try:
        # -------------------------
        # PLACEHOLDER LOGIC (Mock)
        # -------------------------
        verified = True
        confidence = 0.95
        anomalies = []

        # Example anomaly simulation (future vendor output)
        if confidence < 0.5:
            anomalies.append("LOW_CONFIDENCE_IDENTITY")

        # Save result
        state.identity = IdentityResult(
            verified=verified,
            confidence_score=confidence,
            matched_documents=["passport"],
            anomalies=anomalies,
        )

        # -------------------------
        # HARD FAIL RULE
        # -------------------------
        if not verified:
            state.hard_fail_triggered = True
            state.flags.append("IDENTITY_NOT_VERIFIED")
            state.status = KYCStatus.FAILED

        # -------------------------
        # FLAGS FOR REVIEW
        # -------------------------
        for anomaly in anomalies:
            state.flags.append(anomaly)

        state.add_history_entry(
            EventType.IDENTITY_COMPLETE,
            "identity_verification",
            {"verified": verified, "confidence": confidence},
        )

    except Exception as e:
        state.error = str(e)
        state.status = KYCStatus.FAILED
        state.add_history_entry(EventType.IDENTITY_FAILED, "identity_verification", error=str(e))

    return state
