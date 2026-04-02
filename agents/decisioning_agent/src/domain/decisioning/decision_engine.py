"""Deterministic underwriting decision engine."""

from src.domain.reason_codes.reason_selector import select_decline_reasons
from src.services.decision_model.decision_parser import DecisionOutput


INTEREST_RATE_BY_TIER = {
    "A": 7.5,
    "B": 10.0,
    "C": 13.5,
    "D": 18.0,
}


def calculate_disbursement_amount(approved_amount: float) -> float:
    return round(float(approved_amount) * 0.98, 2)


def _calculate_max_approved_amount(
    credit_score_data: dict,
    public_record_data: dict,
    utilization_data: dict,
    inquiry_data: dict,
) -> float:
    base_limit = float(credit_score_data.get("base_limit_band", 0) or 0)
    public_factor = float(public_record_data.get("public_record_adjustment_factor", 1.0) or 1.0)
    utilization_factor = float(utilization_data.get("utilization_adjustment_factor", 1.0) or 1.0)
    inquiry_factor = float(inquiry_data.get("inquiry_penalty_factor", 1.0) or 1.0)
    return round(base_limit * public_factor * utilization_factor * inquiry_factor, 2)


def make_underwriting_decision(
    *,
    aggregated_risk_tier: str,
    credit_score_data: dict,
    public_record_data: dict,
    utilization_data: dict,
    inquiry_data: dict,
    income_data: dict,
    behavior_data: dict | None = None,
    exposure_data: dict | None = None,
    user_request: dict,
) -> DecisionOutput:
    behavior_data = behavior_data or {}
    exposure_data = exposure_data or {}
    requested_amount = float(user_request.get("amount", 0) or 0)
    requested_tenure = int(user_request.get("tenure", 0) or 0)
    hard_decline = bool(public_record_data.get("hard_decline_flag", False))
    affordability_flag = bool(income_data.get("affordability_flag", False))
    max_approved_amount = _calculate_max_approved_amount(
        credit_score_data,
        public_record_data,
        utilization_data,
        inquiry_data,
    )
    interest_rate = INTEREST_RATE_BY_TIER.get(str(aggregated_risk_tier).upper(), 0.0)
    key_factors = []
    if public_record_data.get("hard_decline_flag"):
        key_factors.append("Hard decline public-record trigger")
    if float(income_data.get("estimated_dti", 0) or 0) > 0.45:
        key_factors.append("Debt-to-income ratio above policy threshold")
    if income_data.get("income_missing_flag"):
        key_factors.append("Income requires manual verification")
    if behavior_data.get("chargeoff_history"):
        key_factors.append("Charge-off history detected")
    if utilization_data.get("utilization_risk") in {"HIGH", "CRITICAL"}:
        key_factors.append("Elevated credit utilization")
    if exposure_data.get("exposure_risk") in {"HIGH", "EXTREME"}:
        key_factors.append("High existing debt obligations")

    reasoning_steps = [
        f"Aggregated risk tier evaluated as {aggregated_risk_tier}.",
        f"Calculated maximum approved amount is {max_approved_amount:.2f}.",
        f"Affordability flag is {affordability_flag}.",
    ]

    if str(aggregated_risk_tier).upper() == "F" or hard_decline:
        reasoning_steps.append("Hard decline conditions were met.")
        decline_reasons = select_decline_reasons(
            aggregated_risk_tier=aggregated_risk_tier,
            public_record_data=public_record_data,
            income_data=income_data,
            behavior_data=behavior_data,
            utilization_data=utilization_data,
            exposure_data=exposure_data,
            inquiry_data=inquiry_data,
            credit_score_data=credit_score_data,
        )
        return DecisionOutput(
            decision="DECLINE",
            approved_amount=0.0,
            approved_tenure=0,
            interest_rate=0.0,
            disbursement_amount=0.0,
            explanation="Declined because a hard decline rule or failing risk tier was triggered.",
            reasoning_steps=reasoning_steps,
            confidence_score=1.0,
            key_factors=key_factors[:3],
            **decline_reasons,
        )

    if income_data.get("income_missing_flag"):
        reasoning_steps.append("Income is missing or unverifiable; routing to human review.")
        review_reasons = select_decline_reasons(
            aggregated_risk_tier=aggregated_risk_tier,
            public_record_data=public_record_data,
            income_data=income_data,
            behavior_data=behavior_data,
            utilization_data=utilization_data,
            exposure_data=exposure_data,
            inquiry_data=inquiry_data,
            credit_score_data=credit_score_data,
        )
        return DecisionOutput(
            decision="REFER_TO_HUMAN",
            approved_amount=0.0,
            approved_tenure=0,
            interest_rate=0.0,
            disbursement_amount=0.0,
            explanation="Manual underwriting review is required because income could not be verified automatically.",
            reasoning_steps=reasoning_steps,
            confidence_score=1.0,
            key_factors=key_factors[:3],
            **review_reasons,
        )

    if str(aggregated_risk_tier).upper() == "D" and affordability_flag:
        reasoning_steps.append("Borderline deterministic risk profile routed to human review.")
        review_reasons = select_decline_reasons(
            aggregated_risk_tier=aggregated_risk_tier,
            public_record_data=public_record_data,
            income_data=income_data,
            behavior_data=behavior_data,
            utilization_data=utilization_data,
            exposure_data=exposure_data,
            inquiry_data=inquiry_data,
            credit_score_data=credit_score_data,
        )
        return DecisionOutput(
            decision="REFER_TO_HUMAN",
            approved_amount=0.0,
            approved_tenure=0,
            interest_rate=interest_rate,
            disbursement_amount=0.0,
            explanation="Manual underwriting review is required for this borderline risk profile.",
            reasoning_steps=reasoning_steps,
            confidence_score=1.0,
            key_factors=key_factors[:3],
            **review_reasons,
        )

    if not affordability_flag:
        reasoning_steps.append("Affordability check failed based on DTI.")
        decline_reasons = select_decline_reasons(
            aggregated_risk_tier=aggregated_risk_tier,
            public_record_data=public_record_data,
            income_data=income_data,
            behavior_data=behavior_data,
            utilization_data=utilization_data,
            exposure_data=exposure_data,
            inquiry_data=inquiry_data,
            credit_score_data=credit_score_data,
        )
        return DecisionOutput(
            decision="DECLINE",
            approved_amount=0.0,
            approved_tenure=0,
            interest_rate=0.0,
            disbursement_amount=0.0,
            explanation="Declined because the applicant does not meet affordability requirements.",
            reasoning_steps=reasoning_steps,
            confidence_score=1.0,
            key_factors=key_factors[:3],
            **decline_reasons,
        )

    if requested_amount <= max_approved_amount and max_approved_amount > 0:
        reasoning_steps.append("Requested amount is within deterministic lending capacity.")
        return DecisionOutput(
            decision="APPROVE",
            approved_amount=requested_amount,
            approved_tenure=requested_tenure,
            interest_rate=interest_rate,
            disbursement_amount=calculate_disbursement_amount(requested_amount),
            explanation="Approved within deterministic policy thresholds.",
            reasoning_steps=reasoning_steps,
            confidence_score=1.0,
        )

    reasoning_steps.append("Requested amount exceeds deterministic lending capacity.")
    return DecisionOutput(
        decision="COUNTER_OFFER",
        approved_amount=0.0,
        approved_tenure=0,
        interest_rate=interest_rate,
        disbursement_amount=0.0,
        explanation="Counter offer required because the requested amount exceeds deterministic lending capacity.",
        reasoning_steps=reasoning_steps,
        confidence_score=1.0,
    )
