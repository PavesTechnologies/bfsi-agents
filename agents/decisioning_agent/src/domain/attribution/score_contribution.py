"""Exact contribution reporting for the deterministic weighted score."""


def build_score_contribution(sub_scores: dict, weights: dict) -> list[dict]:
    contributions = []
    for key, weight in weights.items():
        score = float(sub_scores.get(key, 0) or 0)
        contributions.append(
            {
                "component": key,
                "sub_score": score,
                "weight": float(weight),
                "contribution": round(score * float(weight), 4),
            }
        )
    return contributions
