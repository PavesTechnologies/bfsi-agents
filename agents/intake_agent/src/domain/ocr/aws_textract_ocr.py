import boto3
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class OCRBlock:
    text: str
    bbox: Dict[str, float]   # normalized bbox from Textract


@dataclass
class OCRResult:
    full_text: str
    blocks: List[OCRBlock]


_textract = boto3.client("textract")


def extract_ocr_from_bytes(file_bytes: bytes) -> OCRResult:
    """
    AWS Textract OCR for images (JPEG / PNG).
    Uses DetectDocumentText.
    """

    response = _textract.detect_document_text(
        Document={"Bytes": file_bytes}
    )

    blocks = []
    texts = []

    for block in response.get("Blocks", []):
        if block["BlockType"] != "WORD":
            continue

        text = block.get("Text", "")
        bbox = block.get("Geometry", {}).get("BoundingBox", {})

        texts.append(text)
        blocks.append(
            OCRBlock(
                text=text,
                bbox={
                    "left": bbox.get("Left", 0.0),
                    "top": bbox.get("Top", 0.0),
                    "width": bbox.get("Width", 0.0),
                    "height": bbox.get("Height", 0.0),
                },
            )
        )

    return OCRResult(
        full_text=" ".join(texts),
        blocks=blocks,
    )
