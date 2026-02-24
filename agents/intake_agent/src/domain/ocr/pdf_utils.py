# agents/intake_agent/src/domain/ocr/pdf_utils.py


from pdf2image import convert_from_bytes
from PIL import Image


def pdf_bytes_to_images(
    pdf_bytes: bytes,
    dpi: int = 300,
) -> list[Image.Image]:
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
