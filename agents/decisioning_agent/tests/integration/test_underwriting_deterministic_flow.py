import os

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("SERVICE_NAME", "decisioning_agent")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://test:test@localhost:5432/testdb")

from src.domain.decisioning.decision_engine import make_underwriting_decision


def test_underwriting_deterministic_flow_replays_identically():
    kwargs = {
        "aggregated_risk_tier": "B",
        "credit_score_data": {"base_limit_band": 50000, "score": 710},
        "public_record_data": {"public_record_adjustment_factor": 1.0, "hard_decline_flag": False},
        "utilization_data": {"utilization_adjustment_factor": 1.0, "utilization_risk": "GOOD"},
        "inquiry_data": {"inquiry_penalty_factor": 1.0, "inquiries_last_12m": 1},
        "income_data": {"affordability_flag": True, "estimated_dti": 0.31, "income_missing_flag": False},
        "behavior_data": {"chargeoff_history": False, "behavior_risk": "FAIR"},
        "exposure_data": {"exposure_risk": "LOW"},
        "user_request": {"amount": 12000, "tenure": 24},
    }

    first = make_underwriting_decision(**kwargs)
    second = make_underwriting_decision(**kwargs)

    assert first.model_dump() == second.model_dump()
