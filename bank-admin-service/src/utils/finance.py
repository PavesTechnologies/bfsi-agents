from typing import Optional


def compute_emi(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    """Standard reducing-balance EMI formula. Returns monthly instalment rounded to 2dp."""
    r = annual_rate_pct / 12 / 100
    if r == 0:
        return round(principal / tenure_months, 2)
    return round(principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1), 2)


def emi_from_application(
    approved_amount: Optional[float],
    interest_rate: Optional[float],
    tenure_months: Optional[int],
) -> Optional[float]:
    if not all([approved_amount, interest_rate, tenure_months]):
        return None
    return compute_emi(float(approved_amount), float(interest_rate), int(tenure_months))
