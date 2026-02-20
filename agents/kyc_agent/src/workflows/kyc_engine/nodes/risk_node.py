"""
Risk Assessment Node

Third stage of KYC compliance pipeline.
Assesses overall compliance risk and generates final KYC decision.
"""

from datetime import datetime
from src.workflows.kyc_engine.kyc_state import (
    KYCState,
    RiskAssessment,
    FinalDecision,
    EventType,
    RiskLevel,
    KYCDecision,
    KYCStatus,
)


def run_risk(state: KYCState) -> KYCState:
    """Perform risk aggregation using identity + AML results."""

    state.add_history_entry(EventType.RISK_STARTED, "risk_assessment")
    state.current_stage = "risk_assessment"

    try:
        if state.identity is None:
            raise ValueError("Identity must be completed before risk")
        if state.aml is None:
            raise ValueError("AML must be completed before risk")

        # -------------------------
        # HARD FAIL (OFAC)
        # -------------------------
        if state.aml.ofac_match:
            state.hard_fail_triggered = True
            state.flags.append("OFAC_MATCH")

            state.risk = RiskAssessment(
                risk_level=RiskLevel.HIGH,
                risk_score=1.0,
                decision_factors=["OFAC sanction match"],
            )

            state.add_history_entry(
                EventType.RISK_COMPLETE,
                "risk_assessment",
                {"hard_fail": True, "reason": "OFAC_MATCH"},
            )
            return state

        # -------------------------
        # SOFT RISK CALCULATION
        # -------------------------
        risk_score = _calculate_risk_score(
            state.identity.confidence_score,
            state.aml.matches_found,
        )

        if risk_score < 0.3:
            level = RiskLevel.LOW
        elif risk_score < 0.7:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.HIGH

        state.risk = RiskAssessment(
            risk_level=level,
            risk_score=risk_score,
            decision_factors=[],
        )

        state.add_history_entry(
            EventType.RISK_COMPLETE,
            "risk_assessment",
            {"score": risk_score, "level": level.value},
        )

    except Exception as e:
        state.error = str(e)
        state.status = KYCStatus.FAILED
        state.add_history_entry(EventType.RISK_FAILED, "risk_assessment", error=str(e))

    return state


def run_decision(state: KYCState) -> KYCState:
    """Generate final KYC decision."""

    try:
        if state.risk is None:
            raise ValueError("Risk must complete before decision")

        # -------------------------
        # HARD FAIL PRIORITY
        # -------------------------
        if state.hard_fail_triggered:
            decision = KYCDecision.FAIL
            status = KYCStatus.FAILED

        # -------------------------
        # REVIEW CONDITIONS
        # -------------------------
        elif state.aml.pep_match:
            state.flags.append("PEP_MATCH")
            decision = KYCDecision.REVIEW
            status = KYCStatus.REVIEW

        elif state.risk.risk_level == RiskLevel.HIGH:
            decision = KYCDecision.REVIEW
            status = KYCStatus.REVIEW

        # -------------------------
        # PASS
        # -------------------------
        else:
            decision = KYCDecision.PASS
            status = KYCStatus.PASSED

        state.decision = FinalDecision(
            decision=decision,
            rationale="Decision generated from aggregated risk signals",
        )

        state.status = status
        state.completed_at = datetime.utcnow()
        state.confidence_score = state.risk.risk_score

        state.add_history_entry(
            EventType.DECISION_MADE,
            "final_decision",
            {"decision": decision.value},
        )

    except Exception as e:
        state.error = str(e)
        state.status = KYCStatus.FAILED
        state.add_history_entry(EventType.PIPELINE_FAILED, "final_decision", error=str(e))

    return state


def _calculate_risk_score(identity_confidence: float, aml_matches: int) -> float:
    """Simple deterministic risk scoring placeholder."""
    return 0.5 * (1 - identity_confidence) + 0.5 * min(aml_matches / 10, 1.0)
