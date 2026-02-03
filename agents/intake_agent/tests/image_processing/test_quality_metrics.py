import cv2
import numpy as np

from src.domain.image_processing.quality_metrics import (
    brightness_score,
    contrast_score,
    sharpness_score,
    noise_score,
)

def create_dummy_image():
    return np.full((100, 100, 3), 128, dtype=np.uint8)

def test_brightness_score():
    image = create_dummy_image()
    brightness = brightness_score(image)
    assert brightness > 0

def test_contrast_score():
    image = create_dummy_image()
    contrast = contrast_score(image)
    assert contrast >= 0

def test_sharpness_score():
    image = create_dummy_image()
    sharpness = sharpness_score(image)
    assert sharpness >= 0

def test_noise_score():
    image = create_dummy_image()
    noise = noise_score(image)
    assert noise >= 0
