from typing import List
from PIL import Image
import pytesseract

from src.domain.ocr.ocr_result import OCRResult, OCRBlock


def extract_ocr(image: Image.Image) -> OCRResult:
    """
    Extract OCR text and bounding boxes using Tesseract.
    """

    data = pytesseract.image_to_data(
        image, output_type=pytesseract.Output.DICT
    )

    blocks: List[OCRBlock] = []
    texts: List[str] = []

    for i, word in enumerate(data.get("text", [])):
        if not word or not word.strip():
            continue

        x = data["left"][i]
        y = data["top"][i]
        w = data["width"][i]
        h = data["height"][i]

        blocks.append(
            OCRBlock(
                text=word.strip(),
                bbox=(x, y, x + w, y + h),
            )
        )
        texts.append(word.strip())

    return OCRResult(
        full_text=" ".join(texts),
        blocks=blocks,
    )
