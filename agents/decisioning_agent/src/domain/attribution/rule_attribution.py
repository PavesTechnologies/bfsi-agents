"""Human-readable deterministic rule attribution."""


def build_rule_attribution(
    *,
    income_data: dict,
    public_record_data: dict,
    utilization_data: dict,
    exposure_data: dict,
    inquiry_data: dict,
    behavior_data: dict,
) -> list[dict]:
    attribution = []

    dti = float(income_data.get("estimated_dti", 0) or 0)
    if income_data.get("income_missing_flag"):
        attribution.append(
            {
                "rule": "income_verification",
                "description": "Income could not be verified automatically.",
                "metric": "income_missing_flag",
                "value": True,
                "threshold": True,
            }
        )
    elif dti > 0.45:
        attribution.append(
            {
                "rule": "dti_threshold",
                "description": f"DTI {dti:.2f} exceeded threshold 0.45.",
                "metric": "estimated_dti",
                "value": dti,
                "threshold": 0.45,
            }
        )

    bankruptcy_age = public_record_data.get("years_since_bankruptcy")
    if public_record_data.get("bankruptcy_present"):
        attribution.append(
            {
                "rule": "bankruptcy_recency",
                "description": "Bankruptcy history influenced public-record risk handling.",
                "metric": "years_since_bankruptcy",
                "value": bankruptcy_age,
                "threshold": 2,
            }
        )

    if utilization_data.get("utilization_ratio") is not None:
        attribution.append(
            {
                "rule": "utilization_ratio",
                "description": "Revolving utilization contributed to the final risk profile.",
                "metric": "utilization_ratio",
                "value": utilization_data.get("utilization_ratio"),
                "threshold": 0.75,
            }
        )

    if exposure_data.get("monthly_obligation_estimate") is not None:
        attribution.append(
            {
                "rule": "monthly_obligation_estimate",
                "description": "Existing monthly obligations influenced exposure risk.",
                "metric": "monthly_obligation_estimate",
                "value": exposure_data.get("monthly_obligation_estimate"),
                "threshold": "policy exposure tolerance",
            }
        )

    if inquiry_data.get("inquiries_last_12m") is not None:
        attribution.append(
            {
                "rule": "inquiry_velocity",
                "description": "Recent credit inquiries influenced inquiry velocity risk.",
                "metric": "inquiries_last_12m",
                "value": inquiry_data.get("inquiries_last_12m"),
                "threshold": 5,
            }
        )

    if behavior_data.get("behavior_risk") is not None:
        attribution.append(
            {
                "rule": "payment_behavior",
                "description": "Observed payment behavior influenced the final risk profile.",
                "metric": "behavior_risk",
                "value": behavior_data.get("behavior_risk"),
                "threshold": "POOR",
            }
        )

    return attribution
