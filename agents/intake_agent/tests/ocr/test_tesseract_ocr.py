from PIL import Image
from src.domain.ocr.tesseract_ocr import extract_ocr


def test_ocr_extraction():
    image = Image.new("RGB", (300, 100), color="white")

    result = extract_ocr(image)

    assert result is not None
    assert hasattr(result, "full_text")
    assert hasattr(result, "blocks")
