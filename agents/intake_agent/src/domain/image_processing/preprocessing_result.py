from dataclasses import dataclass


@dataclass(frozen=True)
class ImagePreprocessingResult:
    processed_image: bytes
    is_low_quality: bool
    quality_scores: dict[str, float]
