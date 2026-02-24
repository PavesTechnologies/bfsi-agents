import io

import boto3
from PIL import Image
from src.domain.ocr.ocr_types import OCRBlock, OCRResult

# Create Textract client once
_textract = boto3.client("textract")


def extract_ocr(image_or_bytes: bytes | Image.Image) -> OCRResult:
    """
    AWS Textract OCR for images (JPEG / PNG).

    Accepts:
    - raw image bytes
    - PIL Image

    Returns:
    - OCRResult(full_text, blocks)
    """

    # -----------------------------
    # Normalize input to bytes
    # -----------------------------
    if isinstance(image_or_bytes, Image.Image):
        buf = io.BytesIO()
        image_or_bytes.save(buf, format="JPEG")
        image_bytes = buf.getvalue()
    else:
        image_bytes = image_or_bytes

    # -----------------------------
    # Call Textract
    # -----------------------------
    response = _textract.detect_document_text(Document={"Bytes": image_bytes})

    blocks: list[OCRBlock] = []
    text_parts: list[str] = []

    # -----------------------------
    # Parse LINE blocks (not WORD)
    # -----------------------------
    for block in response.get("Blocks", []):
        if block.get("BlockType") != "LINE":
            continue

        text = block.get("Text", "").strip()
        confidence = block.get("Confidence", 0.0)

        geometry = block.get("Geometry", {})
        bbox = geometry.get("BoundingBox", {})

        if not text:
            continue

        text_parts.append(text)

        blocks.append(
            OCRBlock(
                text=text,
                bbox={
                    "left": bbox.get("Left", 0.0),
                    "top": bbox.get("Top", 0.0),
                    "width": bbox.get("Width", 0.0),
                    "height": bbox.get("Height", 0.0),
                },
                confidence=confidence,
            )
        )

    return OCRResult(
        full_text=" ".join(text_parts),
        blocks=blocks,
    )


def extract_ocr_from_bytes(image_bytes: bytes) -> OCRResult:
    """
    Backwards-compatible wrapper accepting raw image bytes.
    """
    return extract_ocr(image_bytes)
