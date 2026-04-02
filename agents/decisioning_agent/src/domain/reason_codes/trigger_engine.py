"""Deterministic trigger engine for reason-code candidates."""

from src.domain.reason_codes.reason_registry import REGULATORY_REASON_MAPPING
from src.domain.reason_codes.reason_types import ReasonSelectionContext, ReasonTriggerResult


def evaluate_reason_triggers(context: ReasonSelectionContext) -> list[ReasonTriggerResult]:
    candidates: list[ReasonTriggerResult] = []

    def add_candidate(
        reason_key: str,
        *,
        trigger_source: str,
        metric_name: str,
        metric_value,
        threshold_value,
        severity: str,
        citation_reference: str,
        internal_rationale: str,
    ) -> None:
        reason = REGULATORY_REASON_MAPPING[reason_key]
        candidates.append(
            ReasonTriggerResult(
                reason_key=reason_key,
                reason_code=reason["reason_code"],
                official_text=reason["official_text"],
                trigger_source=trigger_source,
                metric_name=metric_name,
                metric_value=metric_value,
                threshold_value=threshold_value,
                severity=severity,
                applicable_product=context.product_code,
                citation_reference=citation_reference,
                internal_rationale=internal_rationale,
            )
        )

    years_since_bankruptcy = context.public_record_data.get("years_since_bankruptcy")
    if context.public_record_data.get("bankruptcy_present") and (
        years_since_bankruptcy is None or years_since_bankruptcy < 2
    ):
        add_candidate(
            "BANKRUPTCY_RECENT",
            trigger_source="public_record_data",
            metric_name="years_since_bankruptcy",
            metric_value=years_since_bankruptcy,
            threshold_value=2,
            severity="HIGH",
            citation_reference="5.1",
            internal_rationale="Bankruptcy recency triggered hard-decline policy.",
        )

    if context.public_record_data.get("public_record_severity") == "SEVERE":
        add_candidate(
            "PUBLIC_RECORD_SEVERE",
            trigger_source="public_record_data",
            metric_name="public_record_severity",
            metric_value=context.public_record_data.get("public_record_severity"),
            threshold_value="SEVERE",
            severity="HIGH",
            citation_reference="5.2",
            internal_rationale="Severe public-record classification triggered decline candidate.",
        )

    if context.income_data.get("income_missing_flag"):
        add_candidate(
            "INCOME_UNVERIFIED",
            trigger_source="income_data",
            metric_name="income_missing_flag",
            metric_value=True,
            threshold_value=True,
            severity="HIGH",
            citation_reference="4.3",
            internal_rationale="Income verification failed automated underwriting checks.",
        )
    elif float(context.income_data.get("estimated_dti", 0) or 0) > 0.45:
        add_candidate(
            "DTI_HIGH",
            trigger_source="income_data",
            metric_name="estimated_dti",
            metric_value=float(context.income_data.get("estimated_dti", 0) or 0),
            threshold_value=0.45,
            severity="HIGH",
            citation_reference="4.2",
            internal_rationale="Applicant DTI exceeded policy threshold.",
        )

    tradeline_count = int(context.credit_score_data.get("tradeline_count", 0) or 0) if context.credit_score_data else 0
    credit_age_months = int(context.credit_score_data.get("credit_age_months", 0) or 0) if context.credit_score_data else 0
    if tradeline_count and tradeline_count < 3:
        add_candidate(
            "THIN_FILE",
            trigger_source="credit_score_data",
            metric_name="tradeline_count",
            metric_value=tradeline_count,
            threshold_value=3,
            severity="MEDIUM",
            citation_reference="3.2",
            internal_rationale="Credit file depth does not meet policy minimum.",
        )
        add_candidate(
            "TRADELINE_DEPTH_INSUFFICIENT",
            trigger_source="credit_score_data",
            metric_name="tradeline_count",
            metric_value=tradeline_count,
            threshold_value=3,
            severity="MEDIUM",
            citation_reference="3.2",
            internal_rationale="Active tradeline depth is below policy requirement.",
        )
    if credit_age_months and credit_age_months < 24:
        add_candidate(
            "CREDIT_HISTORY_INSUFFICIENT",
            trigger_source="credit_score_data",
            metric_name="credit_age_months",
            metric_value=credit_age_months,
            threshold_value=24,
            severity="MEDIUM",
            citation_reference="3.2",
            internal_rationale="Credit history length does not meet policy minimum.",
        )

    if context.behavior_data.get("chargeoff_history") or context.behavior_data.get("behavior_risk") in {"POOR", "UNACCEPTABLE"}:
        add_candidate(
            "PAYMENT_BEHAVIOR_POOR",
            trigger_source="behavior_data",
            metric_name="behavior_risk",
            metric_value=context.behavior_data.get("behavior_risk"),
            threshold_value="POOR",
            severity="HIGH",
            citation_reference="6.1",
            internal_rationale="Recent delinquency or charge-off indicators were present.",
        )

    if context.utilization_data.get("utilization_risk") in {"HIGH", "CRITICAL"}:
        add_candidate(
            "UTILIZATION_HIGH",
            trigger_source="utilization_data",
            metric_name="utilization_ratio",
            metric_value=context.utilization_data.get("utilization_ratio"),
            threshold_value=0.75,
            severity="MEDIUM",
            citation_reference="5.3",
            internal_rationale="Utilization exceeded configured risk tolerance.",
        )

    if context.exposure_data.get("exposure_risk") in {"HIGH", "EXTREME"}:
        add_candidate(
            "EXPOSURE_HIGH",
            trigger_source="exposure_data",
            metric_name="exposure_risk",
            metric_value=context.exposure_data.get("exposure_risk"),
            threshold_value="HIGH",
            severity="MEDIUM",
            citation_reference="5.4",
            internal_rationale="Existing obligations exceeded exposure tolerance.",
        )

    if int(context.inquiry_data.get("inquiries_last_12m", 0) or 0) > 5:
        add_candidate(
            "INQUIRIES_EXCESSIVE",
            trigger_source="inquiry_data",
            metric_name="inquiries_last_12m",
            metric_value=int(context.inquiry_data.get("inquiries_last_12m", 0) or 0),
            threshold_value=5,
            severity="LOW",
            citation_reference="6.2",
            internal_rationale="Inquiry velocity exceeded recent-credit-seeking tolerance.",
        )

    if str(context.aggregated_risk_tier).upper() == "F":
        add_candidate(
            "RISK_TIER_F",
            trigger_source="aggregated_risk_tier",
            metric_name="aggregated_risk_tier",
            metric_value=context.aggregated_risk_tier,
            threshold_value="F",
            severity="HIGH",
            citation_reference="7.1",
            internal_rationale="Aggregate policy score fell into decline tier.",
        )

    return sorted(
        candidates,
        key=lambda item: REGULATORY_REASON_MAPPING[item.reason_key]["priority"],
        reverse=True,
    )
