from src.utils.offer_generator import calculate_emi, generate_counter_offer_options


def test_calculate_emi_handles_zero_interest():
    assert calculate_emi(1200.0, 0.0, 12) == 100.0


def test_generate_counter_offer_options_creates_three_variants():
    options = generate_counter_offer_options(
        {
            "approved_amount": 75000.0,
            "approved_tenure_months": 36,
            "interest_rate": 11.5,
        }
    )

    assert [option["offer_id"] for option in options] == [
        "offer_1",
        "offer_2",
        "offer_3",
    ]
    assert options[1]["tenure_months"] == 24
    assert options[2]["tenure_months"] == 48
