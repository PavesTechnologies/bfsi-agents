import cv2
import numpy as np


def to_grayscale(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def brightness_score(image: np.ndarray) -> float:
    gray = to_grayscale(image)
    return float(np.mean(gray))


def contrast_score(image: np.ndarray) -> float:
    gray = to_grayscale(image)
    return float(gray.std())


def sharpness_score(image: np.ndarray) -> float:
    gray = to_grayscale(image)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def noise_score(image: np.ndarray) -> float:
    gray = to_grayscale(image)
    mean = np.mean(gray)
    return float(np.mean((gray - mean) ** 2))


def compute_quality_metrics(image: np.ndarray) -> dict:
    return {
        "brightness": brightness_score(image),
        "contrast": contrast_score(image),
        "sharpness": sharpness_score(image),
        "noise": noise_score(image),
    }
