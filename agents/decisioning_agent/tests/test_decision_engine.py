from src.domain.calculators.dti import (
    affordability_from_dti,
    calculate_dti,
    classify_dti_risk,
)
from src.domain.decisioning.decision_engine import make_underwriting_decision


def test_calculate_dti_and_affordability_for_valid_income():
    dti = calculate_dti(10000, 3000)

    assert dti == 0.3
    assert classify_dti_risk(dti, False) == "MODERATE"
    assert affordability_from_dti(dti, False) is True


def test_calculate_dti_for_missing_income_returns_unacceptable():
    dti = calculate_dti(None, 3000)

    assert dti == 99.9
    assert classify_dti_risk(dti, True) == "UNACCEPTABLE"
    assert affordability_from_dti(dti, True) is False


def test_make_underwriting_decision_approves_when_capacity_and_affordability_pass():
    result = make_underwriting_decision(
        aggregated_risk_tier="B",
        credit_score_data={"base_limit_band": 50000},
        public_record_data={"public_record_adjustment_factor": 1.0, "hard_decline_flag": False},
        utilization_data={"utilization_adjustment_factor": 1.0},
        inquiry_data={"inquiry_penalty_factor": 1.0},
        income_data={"affordability_flag": True},
        user_request={"amount": 10000, "tenure": 24},
    )

    assert result.decision == "APPROVE"
    assert result.interest_rate == 10.0
    assert result.disbursement_amount == 9800.0


def test_make_underwriting_decision_declines_for_hard_decline():
    result = make_underwriting_decision(
        aggregated_risk_tier="B",
        credit_score_data={"base_limit_band": 50000},
        public_record_data={"public_record_adjustment_factor": 1.0, "hard_decline_flag": True},
        utilization_data={"utilization_adjustment_factor": 1.0},
        inquiry_data={"inquiry_penalty_factor": 1.0},
        income_data={"affordability_flag": True},
        user_request={"amount": 10000, "tenure": 24},
    )

    assert result.decision == "DECLINE"
    assert result.disbursement_amount == 0.0


def test_make_underwriting_decision_routes_to_counter_offer_when_amount_exceeds_capacity():
    result = make_underwriting_decision(
        aggregated_risk_tier="C",
        credit_score_data={"base_limit_band": 10000},
        public_record_data={"public_record_adjustment_factor": 0.9, "hard_decline_flag": False},
        utilization_data={"utilization_adjustment_factor": 0.8},
        inquiry_data={"inquiry_penalty_factor": 0.9},
        income_data={"affordability_flag": True},
        user_request={"amount": 10000, "tenure": 24},
    )

    assert result.decision == "COUNTER_OFFER"
    assert result.interest_rate == 13.5
