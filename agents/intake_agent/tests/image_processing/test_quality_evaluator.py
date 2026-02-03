from src.domain.image_processing.quality_evaluator import (
    compute_overall_quality,
    is_low_quality,
)

def test_compute_overall_quality():
    metrics = {
        "brightness": 100,
        "contrast": 50,
        "sharpness": 200,
        "noise": 10,
    }

    score = compute_overall_quality(metrics)
    assert score > 0

def test_low_quality_detection():
    bad_metrics = {
        "brightness": 10,
        "contrast": 5,
        "sharpness": 20,
        "noise": 300,
    }

    assert is_low_quality(bad_metrics) is True
