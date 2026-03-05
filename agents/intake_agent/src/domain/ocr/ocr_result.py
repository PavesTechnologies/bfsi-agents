from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class OCRBlock:
    text: str
    bbox: Tuple[int, int, int, int]  # (x0, y0, x1, y1)


@dataclass(frozen=True)
class OCRResult:
    full_text: str
    blocks: List[OCRBlock]
