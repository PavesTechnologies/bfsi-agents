import torch
from PIL import Image

from src.domain.vision.efficientnet_model import EfficientNetB0
from src.domain.vision.image_preprocessing import preprocess_image
from src.domain.vision.vision_result import VisionClassificationResult


DOCUMENT_LABELS = [
    "passport",
    "drivers_license",
    "pay_stub",
    "w2",
    "bank_statement",
    "utility_bill",
    "unknown",
]


class EfficientNetClassifier:
    def __init__(self, model_path: str | None = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model = EfficientNetB0(num_classes=len(DOCUMENT_LABELS))
        self.model.to(self.device)
        self.model.eval()

        if model_path:
            self.model.load_state_dict(
                torch.load(model_path, map_location=self.device)
            )

    def classify(self, image: Image.Image) -> VisionClassificationResult:
        tensor = preprocess_image(image).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)

        confidence, idx = torch.max(probs, dim=1)

        predicted_label = DOCUMENT_LABELS[idx.item()]
        confidence = confidence.item()

        return VisionClassificationResult(
            document_type=predicted_label,
            confidence=confidence,
            is_valid=confidence >= 0.6,
        )
