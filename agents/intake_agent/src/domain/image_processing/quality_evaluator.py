from .quality_metrics import compute_quality_metrics

QUALITY_WEIGHTS = {
    "brightness": 0.3,
    "contrast": 0.3,
    "sharpness": 0.3,
    "noise": -0.1,
}

LOW_QUALITY_THRESHOLD = 100.0

def compute_overall_quality(metrics: dict) -> float:
    score = 0.0
    for key, weight in QUALITY_WEIGHTS.items():
        score += weight * metrics.get(key, 0.0)
    return float(score)

def is_low_quality(metrics: dict) -> bool:
    return compute_overall_quality(metrics) < LOW_QUALITY_THRESHOLD
