import cv2
import numpy as np


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)  # noqa: E741

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_l = clahe.apply(l)

    merged = cv2.merge((enhanced_l, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
