"""Deterministic debt-to-income calculations."""


def calculate_dti(monthly_income: float | int | None, monthly_obligations: float | int) -> float:
    if monthly_income in (None, 0):
        return 99.9
    return round(float(monthly_obligations) / float(monthly_income), 4)


def classify_dti_risk(dti: float, income_missing: bool) -> str:
    if income_missing:
        return "UNACCEPTABLE"
    if dti < 0.25:
        return "LOW"
    if dti <= 0.35:
        return "MODERATE"
    if dti <= 0.45:
        return "HIGH"
    return "UNACCEPTABLE"


def affordability_from_dti(dti: float, income_missing: bool) -> bool:
    return (not income_missing) and dti <= 0.45
