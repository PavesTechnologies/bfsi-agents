"""Deterministic payment-behavior calculations."""


def _parse_int(value) -> int:
    if value in (None, "", "UNKNOWN"):
        return 0
    return int(str(value).lstrip("0") or "0")


def classify_behavior(tradelines: list[dict], policy_config: dict) -> dict:
    rules = policy_config["payment_behavior"]["delinquency_rules"]
    moderate_threshold = int(rules["moderate_threshold"])
    severe_threshold = int(rules["severe_threshold"])

    total_delinquencies = 0
    chargeoff_history = False

    for trade in tradelines:
        total_delinquencies += _parse_int(trade.get("delinquencies30Days"))
        total_delinquencies += _parse_int(trade.get("delinquencies60Days"))
        total_delinquencies += _parse_int(trade.get("delinquencies90to180Days"))

        derog_counter = _parse_int(trade.get("derogCounter"))
        status = str(trade.get("status", "")).strip()
        if derog_counter > 0 or status in {"97", "93"}:
            chargeoff_history = True

    if chargeoff_history:
        behavior_score = 0.0
        behavior_risk = "UNACCEPTABLE"
    elif total_delinquencies <= 0:
        behavior_score = 100.0
        behavior_risk = "EXCELLENT"
    elif total_delinquencies <= moderate_threshold:
        behavior_score = 75.0
        behavior_risk = "FAIR"
    elif total_delinquencies >= severe_threshold:
        behavior_score = 40.0
        behavior_risk = "POOR"
    else:
        behavior_score = 40.0
        behavior_risk = "POOR"

    return {
        "delinquencies": total_delinquencies,
        "chargeoff_history": chargeoff_history,
        "behavior_score": behavior_score,
        "behavior_risk": behavior_risk,
        "confidence_score": 1.0,
        "model_reasoning": (
            f"Counted {total_delinquencies} delinquencies; "
            f"charge-off history set to {chargeoff_history}."
        ),
    }
