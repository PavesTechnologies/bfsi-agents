# agents/intake_agent/src/domain/ocr/pdf_utils.py

from io import BytesIO
from typing import List

from PIL import Image
from pdf2image import convert_from_bytes


def pdf_bytes_to_images(
    pdf_bytes: bytes,
    dpi: int = 300,
) -> List[Image.Image]:
    """
    Convert PDF bytes into a list of PIL Images.

    - One image per page
    - DPI defaults to 300 for OCR accuracy
    """

    if not pdf_bytes:
        raise ValueError("Empty PDF bytes provided")

    images = convert_from_bytes(
        pdf_bytes,
        dpi=dpi,
        fmt="png",
    )

    return images
