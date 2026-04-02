"""Deterministic loan math helpers."""


def monthly_rate(annual_rate_percent: float) -> float:
    return float(annual_rate_percent) / 12.0 / 100.0


def emi_for_principal(principal: float, annual_rate_percent: float, tenure_months: int) -> float:
    principal = float(principal)
    tenure_months = max(int(tenure_months), 1)
    monthly_interest = monthly_rate(annual_rate_percent)

    if principal <= 0:
        return 0.0
    if monthly_interest == 0:
        return round(principal / tenure_months, 2)

    factor = (1 + monthly_interest) ** tenure_months
    emi = principal * monthly_interest * factor / (factor - 1)
    return round(emi, 2)


def principal_for_emi(max_emi: float, annual_rate_percent: float, tenure_months: int) -> float:
    max_emi = float(max_emi)
    tenure_months = max(int(tenure_months), 1)
    monthly_interest = monthly_rate(annual_rate_percent)

    if max_emi <= 0:
        return 0.0
    if monthly_interest == 0:
        return round(max_emi * tenure_months, 2)

    principal = max_emi * ((1 - (1 + monthly_interest) ** (-tenure_months)) / monthly_interest)
    return round(principal, 2)
