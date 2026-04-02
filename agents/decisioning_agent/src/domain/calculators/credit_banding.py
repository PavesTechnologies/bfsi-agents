"""Deterministic credit score banding and limit assignment."""


def _normalize_band_name(raw_band_name: str) -> str:
    mapping = {
        "excellent": "PRIME",
        "good": "NEAR_PRIME",
        "fair": "FAIR",
        "poor": "SUBPRIME",
        "very_poor": "SUBPRIME",
    }
    return mapping.get(raw_band_name.lower(), raw_band_name.upper())


def _normalize_risk_flag(raw_risk: str) -> str:
    mapping = {
        "LOW_MODERATE": "MODERATE",
        "VERY_HIGH": "HIGH",
    }
    return mapping.get(raw_risk.upper(), raw_risk.upper())


def classify_credit_score(score: int, policy_config: dict) -> dict:
    credit_policy = policy_config["credit_score"]["bands"]

    for band_name, config in credit_policy.items():
        if int(config["min"]) <= score <= int(config["max"]):
            return {
                "score": score,
                "score_band": _normalize_band_name(band_name),
                "base_limit_band": float(config["base_limit"]),
                "score_risk_flag": _normalize_risk_flag(config["risk"]),
                "score_weight": 0.25,
                "confidence_score": 1.0,
                "model_reasoning": (
                    f"Score {score} falls into configured band '{band_name}' "
                    f"with base limit {config['base_limit']}."
                ),
            }

    return {
        "score": score,
        "score_band": "SUBPRIME",
        "base_limit_band": 0.0,
        "score_risk_flag": "HIGH",
        "score_weight": 0.25,
        "confidence_score": 0.5,
        "model_reasoning": "Score did not match a configured band; defaulted conservatively.",
    }
