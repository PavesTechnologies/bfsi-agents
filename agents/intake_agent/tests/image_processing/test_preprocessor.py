import cv2
from pathlib import Path

from src.domain.image_processing.preprocessor import preprocess

SAMPLES_DIR = Path(__file__).parent / "samples"

def load_image_bytes(filename: str) -> bytes:
    path = SAMPLES_DIR / filename
    with open(path, "rb") as f:
        return f.read()

def test_preprocess_clean_document():
    image_bytes = load_image_bytes("clean_document.jpg")
    result = preprocess(image_bytes)

    assert result.processed_image is not None
    assert isinstance(result.is_low_quality, bool)
    assert "overall_quality" in result.quality_scores

def test_low_quality_flagging():
    image_bytes = load_image_bytes("dark_image.jpg")
    result = preprocess(image_bytes)

    assert result.is_low_quality is True
