from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class ImagePreprocessingResult:
    processed_image: bytes
    is_low_quality: bool
    quality_scores: Dict[str, float]
