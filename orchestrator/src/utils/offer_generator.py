"""Helpers for deriving counter-offer choices."""

from typing import Any, Dict, List


def calculate_emi(principal: float, annual_rate: float, months: int) -> float:
    """Calculate the monthly EMI for the supplied loan terms."""
    if months <= 0:
        raise ValueError("months must be greater than zero")

    monthly_rate = annual_rate / (12 * 100)
    if monthly_rate == 0:
        return round(principal / months, 2)

    factor = (1 + monthly_rate) ** months
    return round(principal * monthly_rate * factor / (factor - 1), 2)


def generate_counter_offer_options(uw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate fallback counter-offer options from a base underwriting response."""
    base_amount = float(uw_data["approved_amount"])
    base_tenure = int(uw_data["approved_tenure_months"])
    base_rate = float(uw_data["interest_rate"])

    shorter_tenure = max(12, base_tenure - 12)
    longer_tenure = base_tenure + 12
    higher_rate = round(base_rate + 0.5, 2)

    return [
        {
            "offer_id": "offer_1",
            "principal_amount": base_amount,
            "tenure_months": base_tenure,
            "interest_rate": base_rate,
            "monthly_emi": calculate_emi(base_amount, base_rate, base_tenure),
            "label": "Recommended",
        },
        {
            "offer_id": "offer_2",
            "principal_amount": base_amount,
            "tenure_months": shorter_tenure,
            "interest_rate": base_rate,
            "monthly_emi": calculate_emi(base_amount, base_rate, shorter_tenure),
            "label": "Pay Faster",
        },
        {
            "offer_id": "offer_3",
            "principal_amount": base_amount,
            "tenure_months": longer_tenure,
            "interest_rate": higher_rate,
            "monthly_emi": calculate_emi(base_amount, higher_rate, longer_tenure),
            "label": "Lower EMI",
        },
    ]
