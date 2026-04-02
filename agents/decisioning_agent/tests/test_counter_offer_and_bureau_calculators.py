from src.domain.calculators.counter_offer import generate_counter_offer
from src.domain.calculators.inquiry_velocity import classify_inquiry_velocity
from src.domain.calculators.utilization import classify_utilization
from src.policy.policy_loader import load_policy_config


def test_generate_counter_offer_returns_multiple_affordable_options():
    result = generate_counter_offer(
        risk_tier="C",
        base_limit=35000,
        requested_amount=50000,
        requested_tenure=24,
        monthly_income=12000,
        monthly_obligations=2500,
        original_request_dti=0.48,
    )

    assert result["max_affordable_emi"] > 0
    assert len(result["generated_options"]) >= 2
    assert all(option["monthly_payment_emi"] <= result["max_affordable_emi"] + 1 for option in result["generated_options"])


def test_generate_counter_offer_uses_conservative_fallback_when_income_missing():
    result = generate_counter_offer(
        risk_tier="D",
        base_limit=20000,
        requested_amount=30000,
        requested_tenure=24,
        monthly_income=0,
        monthly_obligations=0,
        original_request_dti=99.9,
    )

    assert result["max_affordable_emi"] == round(20000 / 60.0, 2)
    assert len(result["generated_options"]) >= 1


def test_classify_utilization_uses_policy_bands():
    revolving_trades = [
        {
            "balanceAmount": "00002000",
            "enhancedPaymentData": {"creditLimitAmount": "000010000"},
            "revolvingOrInstallment": "R",
        },
        {
            "balanceAmount": "00001000",
            "enhancedPaymentData": {"creditLimitAmount": "000005000"},
            "revolvingOrInstallment": "R",
        },
    ]

    result = classify_utilization(revolving_trades, load_policy_config())

    assert result["total_credit_limit"] == 15000.0
    assert result["total_balance"] == 3000.0
    assert result["utilization_ratio"] == 0.2
    assert result["utilization_risk"] == "EXCELLENT"


def test_classify_inquiry_velocity_counts_last_12_months():
    policy = load_policy_config()
    result = classify_inquiry_velocity(
        [
            {"date": "01012026"},
            {"date": "07012025"},
            {"date": "01012024"},
        ],
        policy,
    )

    assert result["inquiries_last_12m"] >= 2
    assert result["velocity_risk"] in {"LOW", "MODERATE", "HIGH"}
