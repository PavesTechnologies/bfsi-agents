"""Deterministic revolving utilization calculations."""


def _parse_numeric(value) -> float:
    if value in (None, "", "UNKNOWN"):
        return 0.0
    return float(str(value).lstrip("0") or "0")


def classify_utilization(revolving_trades: list[dict], policy_config: dict) -> dict:
    total_credit_limit = 0.0
    total_balance = 0.0

    for trade in revolving_trades:
        enhanced = trade.get("enhancedPaymentData", {})
        total_credit_limit += _parse_numeric(enhanced.get("creditLimitAmount"))
        total_balance += _parse_numeric(trade.get("balanceAmount"))

    utilization_ratio = round(total_balance / total_credit_limit, 4) if total_credit_limit > 0 else 0.0
    bands = policy_config["utilization"]["bands"]

    if utilization_ratio <= float(bands["low"]["max"]):
        risk = "EXCELLENT"
        factor = float(bands["low"]["factor"])
    elif utilization_ratio <= float(bands["moderate"]["max"]):
        risk = "GOOD"
        factor = float(bands["moderate"]["factor"])
    elif utilization_ratio <= float(bands["high"]["max"]):
        risk = "HIGH"
        factor = float(bands["high"]["factor"])
    else:
        risk = "CRITICAL"
        factor = float(bands["very_high"]["factor"])

    return {
        "total_credit_limit": round(total_credit_limit, 2),
        "total_balance": round(total_balance, 2),
        "utilization_ratio": utilization_ratio,
        "utilization_risk": risk,
        "utilization_adjustment_factor": factor,
        "confidence_score": 1.0,
        "model_reasoning": (
            f"Computed revolving utilization as {utilization_ratio:.4f} "
            f"from balance {total_balance:.2f} and credit limit {total_credit_limit:.2f}."
        ),
    }
