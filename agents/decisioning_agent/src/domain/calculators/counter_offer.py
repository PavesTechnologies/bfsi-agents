"""Deterministic counter-offer generation."""

from src.domain.calculators.loan_math import emi_for_principal, principal_for_emi


INTEREST_RATE_BY_TIER = {
    "A": 7.5,
    "B": 10.0,
    "C": 13.5,
    "D": 18.0,
}


def _disbursement_amount(principal: float) -> float:
    return round(float(principal) * 0.98, 2)


def _build_option(option_id: str, description: str, principal: float, tenure: int, rate: float) -> dict:
    principal = round(max(principal, 0.0), 2)
    tenure = max(int(tenure), 1)
    monthly_payment = emi_for_principal(principal, rate, tenure)
    return {
        "option_id": option_id,
        "description": description,
        "proposed_amount": principal,
        "proposed_tenure_months": tenure,
        "proposed_interest_rate": rate,
        "disbursement_amount": _disbursement_amount(principal),
        "monthly_payment_emi": monthly_payment,
        "total_repayment": round(monthly_payment * tenure, 2),
    }


def generate_counter_offer(
    *,
    risk_tier: str,
    base_limit: float,
    requested_amount: float,
    requested_tenure: int,
    monthly_income: float,
    monthly_obligations: float,
    original_request_dti: float,
) -> dict:
    rate = INTEREST_RATE_BY_TIER.get(str(risk_tier).upper(), 18.0)
    requested_tenure = max(int(requested_tenure), 12)
    base_limit = max(float(base_limit), 0.0)
    requested_amount = max(float(requested_amount), 0.0)
    monthly_income = max(float(monthly_income), 0.0)
    monthly_obligations = max(float(monthly_obligations), 0.0)

    if monthly_income > 0:
        max_affordable_emi = max(round((monthly_income * 0.40) - monthly_obligations, 2), 0.0)
    else:
        max_affordable_emi = round(base_limit / 60.0, 2)

    reduced_same_tenure = min(
        principal_for_emi(max_affordable_emi, rate, requested_tenure),
        base_limit or requested_amount,
    )
    extended_tenure = max(requested_tenure + 12, 36)
    longer_term_amount = min(
        principal_for_emi(max_affordable_emi, rate, extended_tenure),
        base_limit or requested_amount,
    )
    minimum_viable_amount = min(base_limit * 0.5 if base_limit else requested_amount * 0.5, longer_term_amount or reduced_same_tenure)

    options = [
        _build_option(
            "OPT_REDUCED_AMOUNT",
            "Reduce principal while keeping the requested tenure.",
            reduced_same_tenure,
            requested_tenure,
            rate,
        ),
        _build_option(
            "OPT_EXTENDED_TERM",
            "Extend the repayment term to reduce monthly obligation.",
            longer_term_amount,
            extended_tenure,
            rate,
        ),
    ]

    if minimum_viable_amount > 0:
        options.append(
            _build_option(
                "OPT_MINIMUM_VIABLE",
                "Offer a smaller practical amount with a comfortable term.",
                minimum_viable_amount,
                max(extended_tenure, 48),
                rate,
            )
        )

    # Keep distinct non-zero options only, preserving order.
    unique_options = []
    seen = set()
    for option in options:
        signature = (option["proposed_amount"], option["proposed_tenure_months"])
        if option["proposed_amount"] <= 0 or signature in seen:
            continue
        seen.add(signature)
        unique_options.append(option)

    return {
        "original_request_dti": float(original_request_dti),
        "max_affordable_emi": max_affordable_emi,
        "counter_offer_logic": (
            "Original request exceeded deterministic lending capacity; "
            "alternatives were generated from affordability and term constraints."
        ),
        "generated_options": unique_options[:3],
        "confidence_score": 1.0,
    }
