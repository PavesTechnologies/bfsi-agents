"""Deterministic debt exposure calculations."""


def _parse_numeric(value) -> float:
    if value in (None, "", "UNKNOWN"):
        return 0.0
    return float(str(value).lstrip("0") or "0")


def classify_exposure(open_trades: list[dict]) -> dict:
    total_existing_debt = 0.0
    monthly_obligation_estimate = 0.0

    for trade in open_trades:
        balance = _parse_numeric(trade.get("balanceAmount"))
        total_existing_debt += balance

        monthly_payment = _parse_numeric(trade.get("monthlyPaymentAmount"))
        if monthly_payment > 0:
            monthly_obligation_estimate += monthly_payment
            continue

        remaining_terms = _parse_numeric(trade.get("terms"))
        if balance > 0 and remaining_terms > 0:
            monthly_obligation_estimate += balance / remaining_terms

    total_existing_debt = round(total_existing_debt, 2)
    monthly_obligation_estimate = round(monthly_obligation_estimate, 2)

    if monthly_obligation_estimate < 500:
        exposure_risk = "LOW"
    elif monthly_obligation_estimate <= 1500:
        exposure_risk = "MODERATE"
    elif monthly_obligation_estimate <= 3500:
        exposure_risk = "HIGH"
    else:
        exposure_risk = "EXTREME"

    return {
        "total_existing_debt": total_existing_debt,
        "monthly_obligation_estimate": monthly_obligation_estimate,
        "exposure_risk": exposure_risk,
        "confidence_score": 1.0,
        "model_reasoning": (
            f"Computed total existing debt {total_existing_debt:.2f} and "
            f"monthly obligations {monthly_obligation_estimate:.2f}."
        ),
    }
