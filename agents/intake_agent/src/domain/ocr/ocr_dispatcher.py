import io

from PIL import Image
from src.domain.ocr.aws_textract_ocr import (
    OCRResult,
    extract_ocr_from_bytes,
)
from src.domain.ocr.pdf_utils import pdf_bytes_to_images


def extract_ocr(file_bytes: bytes, mime_type: str) -> OCRResult:
    """
    Unified OCR entrypoint.
    AWS Textract ONLY.
    """

    if mime_type == "application/pdf":
        images = pdf_bytes_to_images(file_bytes)

        results = [extract_ocr_from_bytes(_image_to_bytes(img)) for img in images]

        full_text = " ".join(r.full_text for r in results)
        blocks = [b for r in results for b in r.blocks]

        return OCRResult(full_text, blocks)

    # image (jpeg/png)
    return extract_ocr_from_bytes(file_bytes)


def _image_to_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()
