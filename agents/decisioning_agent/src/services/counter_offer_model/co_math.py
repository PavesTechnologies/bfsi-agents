"""
Counter-Offer Math Helpers

Pure EMI arithmetic used by the counter-offer engine.
No state, no I/O, no LLM — deterministic by design.
"""

import math


def compute_emi(principal: float, annual_rate: float, months: int) -> float:
    """Standard reducing-balance EMI formula.

    EMI = P × r × (1+r)^n / ((1+r)^n - 1)
    where r = annual_rate / (12 × 100), n = months
    """
    if months <= 0:
        raise ValueError(f"months must be > 0, got {months}")
    r = annual_rate / (12 * 100)
    if r == 0:
        return round(principal / months, 2)
    factor = (1 + r) ** months
    return round(principal * r * factor / (factor - 1), 2)


def compute_max_principal(max_emi: float, monthly_rate: float, months: int) -> float:
    """Back-solve: largest principal whose EMI does not exceed max_emi.

    Rearranges EMI formula to solve for P given EMI, r, and n.
    P = EMI × ((1+r)^n - 1) / (r × (1+r)^n)
    """
    if months <= 0:
        raise ValueError(f"months must be > 0, got {months}")
    if monthly_rate == 0:
        return round(max_emi * months, 2)
    factor = (1 + monthly_rate) ** months
    return round(max_emi * (factor - 1) / (monthly_rate * factor), 2)


def compute_max_affordable_emi(
    monthly_income: float,
    existing_obligations: float,
    foir_pct: float,
    min_disposable_pct: float,
) -> float:
    """Income-driven affordability ceiling (max EMI the applicant can service).

        gross_capacity = monthly_income × foir_pct / 100      (tier-driven FOIR)
        disposable     = gross_capacity − existing_obligations
        floor          = monthly_income × min_disposable_pct / 100
        result         = max(disposable, floor)

    The floor guarantees the ceiling is never ≤ 0 for an applicant who has
    income, even when existing obligations are high. Returns 0.0 only when
    monthly_income ≤ 0 (no income on file → cannot assess affordability).
    """
    if monthly_income <= 0:
        return 0.0
    gross_capacity = monthly_income * foir_pct / 100.0
    disposable = gross_capacity - existing_obligations
    floor = monthly_income * min_disposable_pct / 100.0
    return round(max(disposable, floor), 2)


def compute_co2_tenure(
    principal: float, annual_rate: float, max_emi: float
) -> tuple[bool, int]:
    """Find the minimum tenure (months) such that EMI <= max_emi.

    Solves for n in the EMI formula:
        n = -log(1 - P×r / max_emi) / log(1 + r)

    Returns (feasible, tenure_months).
    Infeasible when monthly interest alone (P × r) already exceeds max_emi,
    meaning no finite tenure can bring the EMI within affordability.
    """
    r = annual_rate / (12 * 100)
    if r == 0:
        return True, math.ceil(principal / max_emi)
    inner = 1.0 - (principal * r / max_emi)
    if inner <= 0:
        return False, 0
    n = math.ceil(-math.log(inner) / math.log(1 + r))
    return True, n
