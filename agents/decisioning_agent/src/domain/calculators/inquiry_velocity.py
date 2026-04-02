"""Deterministic inquiry velocity calculations."""

from datetime import datetime


def _parse_date(raw_date: str | None) -> datetime | None:
    if not raw_date:
        return None
    raw_date = str(raw_date).strip()
    for fmt in ("%m%d%Y", "%m/%d/%Y", "%Y-%m-%d", "%m%d%y"):
        try:
            return datetime.strptime(raw_date, fmt)
        except ValueError:
            continue
    return None


def classify_inquiry_velocity(inquiries: list[dict], policy_config: dict) -> dict:
    now = datetime.now()
    last_12_months = 0
    for inquiry in inquiries:
        inquiry_date = _parse_date(inquiry.get("date"))
        if inquiry_date is None:
            continue
        age_days = (now - inquiry_date).days
        if 0 <= age_days <= 365:
            last_12_months += 1

    bands = policy_config["inquiry_velocity"]["bands"]
    if last_12_months <= int(bands["low"]["max_last_12m"]):
        risk = "LOW"
        factor = float(bands["low"]["factor"])
    elif last_12_months <= int(bands["elevated"]["max_last_12m"]):
        risk = "MODERATE"
        factor = float(bands["elevated"]["factor"])
    elif last_12_months <= int(bands["high"]["max_last_12m"]):
        risk = "HIGH"
        factor = float(bands["high"]["factor"])
    else:
        risk = "HIGH"
        factor = float(bands["very_high"]["factor"])

    return {
        "inquiries_last_12m": last_12_months,
        "velocity_risk": risk,
        "inquiry_penalty_factor": factor,
        "confidence_score": 1.0,
        "model_reasoning": f"Counted {last_12_months} inquiries in the last 12 months.",
    }
