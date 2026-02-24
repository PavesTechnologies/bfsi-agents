import cv2
import numpy as np


def denoise(image: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoisingColored(
        image, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21
    )
