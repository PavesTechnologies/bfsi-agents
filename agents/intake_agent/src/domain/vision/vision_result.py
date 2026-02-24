from dataclasses import dataclass


@dataclass
class VisionClassificationResult:
    document_type: str
    confidence: float
    is_valid: bool
    model: str = "efficientnet_b0"
