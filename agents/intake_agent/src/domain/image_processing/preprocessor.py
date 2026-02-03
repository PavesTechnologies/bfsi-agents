import cv2
import numpy as np

from .deskew import deskew
from .noise_reduction import denoise
from .contrast import enhance_contrast
from .quality_metrics import compute_quality_metrics
from .quality_evaluator import (
    is_low_quality,
    compute_overall_quality,
)
from .preprocessing_result import ImagePreprocessingResult


def preprocess(image_bytes: bytes) -> ImagePreprocessingResult:
    """
    Preprocess an uploaded document image for OCR readiness.

    Steps (in order):
    1. Decode image bytes
    2. Compute quality metrics on original image
    3. Flag low-quality images (non-blocking)
    4. Deskew image
    5. Reduce noise
    6. Enhance contrast (CLAHE)
    7. Encode processed image

    This function MUST be:
    - deterministic
    - side-effect free
    - OCR-agnostic
    """

    # --- Decode image bytes ---
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Invalid image bytes provided for preprocessing")

    # --- Quality metrics on ORIGINAL image ---
    metrics = compute_quality_metrics(image)
    overall_quality = compute_overall_quality(metrics)
    low_quality_flag = is_low_quality(metrics)

    # --- Image preprocessing pipeline ---
    processed = deskew(image)
    processed = denoise(processed)
    processed = enhance_contrast(processed)

    # --- Encode processed image ---
    success, encoded = cv2.imencode(".png", processed)
    if not success:
        raise ValueError("Failed to encode processed image")

    # --- Assemble domain result ---
    return ImagePreprocessingResult(
        processed_image=encoded.tobytes(),
        is_low_quality=low_quality_flag,
        quality_scores={
            **metrics,
            "overall_quality": overall_quality,
        },
    )
