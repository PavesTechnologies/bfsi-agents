import os

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")

from src.domain.decisioning.decision_engine import make_underwriting_decision


def test_human_review_routing_for_missing_income():
    result = make_underwriting_decision(
        aggregated_risk_tier="C",
        credit_score_data={"base_limit_band": 35000, "score": 680},
        public_record_data={"public_record_adjustment_factor": 1.0, "hard_decline_flag": False},
        utilization_data={"utilization_adjustment_factor": 1.0, "utilization_risk": "GOOD"},
        inquiry_data={"inquiry_penalty_factor": 1.0, "inquiries_last_12m": 1},
        income_data={"affordability_flag": False, "estimated_dti": 99.9, "income_missing_flag": True},
        behavior_data={"chargeoff_history": False, "behavior_risk": "FAIR"},
        exposure_data={"exposure_risk": "LOW"},
        user_request={"amount": 9000, "tenure": 18},
    )

    assert result.decision == "REFER_TO_HUMAN"
    assert result.primary_reason_key == "INCOME_UNVERIFIED"
