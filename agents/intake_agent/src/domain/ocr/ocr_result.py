from dataclasses import dataclass


@dataclass(frozen=True)
class OCRBlock:
    text: str
    bbox: tuple[int, int, int, int]  # (x0, y0, x1, y1)


@dataclass(frozen=True)
class OCRResult:
    full_text: str
    blocks: list[OCRBlock]
