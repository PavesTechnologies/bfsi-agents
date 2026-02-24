from dataclasses import dataclass


@dataclass
class OCRBlock:
    text: str
    bbox: dict[str, float]  # normalized: left, top, width, height
    confidence: float


@dataclass
class OCRResult:
    full_text: str
    blocks: list[OCRBlock]
