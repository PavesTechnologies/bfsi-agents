from pdf2image import convert_from_bytes
from PIL import Image


def pdf_bytes_to_images(pdf_bytes: bytes) -> list[Image.Image]:
    """
    Convert PDF bytes to a list of PIL Images (one per page).
    """
    return convert_from_bytes(pdf_bytes, dpi=300)
