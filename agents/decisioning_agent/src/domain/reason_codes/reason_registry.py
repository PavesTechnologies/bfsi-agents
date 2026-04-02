"""Controlled regulatory reason mapping for underwriting declines."""

REGULATORY_REASON_MAPPING = {
    "BANKRUPTCY_RECENT": {
        "reason_code": "PR01",
        "official_text": "Recent bankruptcy on file",
        "priority": 100,
        "trigger_logic": "bankruptcy_present and years_since_bankruptcy < 2",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "PUBLIC_RECORD_SEVERE": {
        "reason_code": "PR02",
        "official_text": "Adverse public record history",
        "priority": 90,
        "trigger_logic": "public_record_severity == SEVERE",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "DTI_HIGH": {
        "reason_code": "01",
        "official_text": "Debt-to-income ratio too high",
        "priority": 95,
        "trigger_logic": "estimated_dti > 0.45",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "INCOME_UNVERIFIED": {
        "reason_code": "04",
        "official_text": "Unable to verify income",
        "priority": 98,
        "trigger_logic": "income_missing_flag is true",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "PAYMENT_BEHAVIOR_POOR": {
        "reason_code": "03",
        "official_text": "Delinquency on accounts with us or others",
        "priority": 85,
        "trigger_logic": "chargeoff_history or behavior_risk in {POOR, UNACCEPTABLE}",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "UTILIZATION_HIGH": {
        "reason_code": "UT01",
        "official_text": "Credit utilization too high",
        "priority": 70,
        "trigger_logic": "utilization_risk in {HIGH, CRITICAL}",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "EXPOSURE_HIGH": {
        "reason_code": "EX01",
        "official_text": "Existing debt obligations are too high",
        "priority": 75,
        "trigger_logic": "exposure_risk in {HIGH, EXTREME}",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "INQUIRIES_EXCESSIVE": {
        "reason_code": "IN01",
        "official_text": "Too many recent credit inquiries",
        "priority": 60,
        "trigger_logic": "inquiries_last_12m > 5",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "RISK_TIER_F": {
        "reason_code": "RK01",
        "official_text": "Overall risk assessment does not meet policy threshold",
        "priority": 50,
        "trigger_logic": "aggregated_risk_tier == F",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "CREDIT_HISTORY_INSUFFICIENT": {
        "reason_code": "02",
        "official_text": "Limited credit experience",
        "priority": 82,
        "trigger_logic": "tradeline_count < 3 or credit_age_months < 24",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "THIN_FILE": {
        "reason_code": "TF01",
        "official_text": "Credit file does not contain sufficient depth",
        "priority": 78,
        "trigger_logic": "tradeline_count < 3",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "POLICY_EXCEPTION_REQUIRED": {
        "reason_code": "PE01",
        "official_text": "Application requires policy exception review",
        "priority": 77,
        "trigger_logic": "manual policy exception required",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "INCOME_INSTABILITY": {
        "reason_code": "04A",
        "official_text": "Income patterns do not meet policy stability requirements",
        "priority": 74,
        "trigger_logic": "income_stability_flag is false",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
    "COLLATERAL_INSUFFICIENT": {
        "reason_code": "05",
        "official_text": "Value or type of collateral not sufficient",
        "priority": 40,
        "trigger_logic": "ltv > threshold or property type excluded",
        "applicable_products": ["SECURED_LOAN"],
    },
    "LTV_HIGH": {
        "reason_code": "05A",
        "official_text": "Loan-to-value ratio too high",
        "priority": 41,
        "trigger_logic": "ltv > threshold",
        "applicable_products": ["SECURED_LOAN"],
    },
    "TRADELINE_DEPTH_INSUFFICIENT": {
        "reason_code": "TD01",
        "official_text": "Insufficient number of active credit tradelines",
        "priority": 79,
        "trigger_logic": "tradeline_count < minimum required tradelines",
        "applicable_products": ["UNSECURED_PERSONAL_LOAN"],
    },
}


def reason_details(reason_key: str) -> dict:
    if reason_key not in REGULATORY_REASON_MAPPING:
        raise ValueError(f"Unknown regulatory reason key: {reason_key}")
    reason = REGULATORY_REASON_MAPPING[reason_key]
    return {
        "reason_key": reason_key,
        "reason_code": reason["reason_code"],
        "official_text": reason["official_text"],
    }
