from dataclasses import dataclass
from typing import List, Dict


@dataclass
class OCRBlock:
    text: str
    bbox: Dict[str, float]  # normalized: left, top, width, height
    confidence: float


@dataclass
class OCRResult:
    full_text: str
    blocks: List[OCRBlock]
