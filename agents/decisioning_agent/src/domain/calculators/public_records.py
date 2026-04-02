"""Deterministic public-record classification."""

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


def _years_since(date_value: datetime | None) -> int | None:
    if date_value is None:
        return None
    today = datetime.now()
    years = today.year - date_value.year
    if (today.month, today.day) < (date_value.month, date_value.day):
        years -= 1
    return max(years, 0)


def classify_public_records(public_records: list[dict], policy_config: dict) -> dict:
    bankruptcy_policy = policy_config["public_records"]["bankruptcy"]
    hard_decline_years = int(bankruptcy_policy["hard_decline_if_within_years"])

    if not public_records:
        return {
            "bankruptcy_present": False,
            "years_since_bankruptcy": None,
            "public_record_severity": "NONE",
            "public_record_adjustment_factor": 1.0,
            "hard_decline_flag": False,
            "confidence_score": 1.0,
            "model_reasoning": "No public records found.",
        }

    bankruptcy_records = [record for record in public_records if record.get("filingDate")]
    bankruptcy_present = bool(bankruptcy_records)

    if not bankruptcy_present:
        return {
            "bankruptcy_present": False,
            "years_since_bankruptcy": None,
            "public_record_severity": "LOW",
            "public_record_adjustment_factor": 0.9,
            "hard_decline_flag": False,
            "confidence_score": 1.0,
            "model_reasoning": "Public records exist without a bankruptcy filing date; classified conservatively as LOW.",
        }

    parsed_dates = [
        _parse_date(record.get("filingDate"))
        for record in bankruptcy_records
    ]
    parsed_dates = [date_value for date_value in parsed_dates if date_value is not None]
    latest_bankruptcy = max(parsed_dates) if parsed_dates else None
    years_since_bankruptcy = _years_since(latest_bankruptcy)
    multiple_records = len(public_records) > 1

    if years_since_bankruptcy is None:
        severity = "SEVERE"
        factor = 0.5
        hard_decline = True
    elif years_since_bankruptcy <= 5 or multiple_records:
        severity = "SEVERE"
        factor = 0.5
        hard_decline = years_since_bankruptcy < hard_decline_years or severity == "SEVERE"
    else:
        severity = "MODERATE"
        factor = 0.75
        hard_decline = years_since_bankruptcy < hard_decline_years

    return {
        "bankruptcy_present": True,
        "years_since_bankruptcy": years_since_bankruptcy,
        "public_record_severity": severity,
        "public_record_adjustment_factor": factor,
        "hard_decline_flag": hard_decline,
        "confidence_score": 1.0 if years_since_bankruptcy is not None else 0.6,
        "model_reasoning": (
            f"Most recent bankruptcy is {years_since_bankruptcy} years old; "
            f"classified as {severity} with factor {factor}."
            if years_since_bankruptcy is not None
            else "Bankruptcy filing date could not be parsed; classified conservatively."
        ),
    }
