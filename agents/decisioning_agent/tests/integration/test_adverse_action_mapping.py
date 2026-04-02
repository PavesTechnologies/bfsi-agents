import os

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")

from src.domain.reason_codes.reason_selector import select_decline_reasons


def test_adverse_action_mapping_produces_candidate_and_selected_reasons():
    result = select_decline_reasons(
        aggregated_risk_tier="F",
        public_record_data={"bankruptcy_present": True, "years_since_bankruptcy": 1, "public_record_severity": "SEVERE"},
        income_data={"estimated_dti": 0.58, "income_missing_flag": False},
        behavior_data={"chargeoff_history": True, "behavior_risk": "POOR"},
        utilization_data={"utilization_risk": "HIGH", "utilization_ratio": 0.8},
        exposure_data={"exposure_risk": "HIGH"},
        inquiry_data={"inquiries_last_12m": 7},
        credit_score_data={"tradeline_count": 2, "credit_age_months": 12},
    )

    assert result["primary_reason_key"]
    assert result["secondary_reason_key"]
    assert len(result["candidate_reason_codes"]) >= 2
    assert len(result["selected_reason_codes"]) == 2
