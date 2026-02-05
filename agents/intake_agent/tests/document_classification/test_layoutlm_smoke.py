from PIL import Image
from src.domain.document_classification.ml.layoutlm_classifier import (
    LayoutLMClassifier
)


def test_layoutlm_smoke():
    image = Image.new("RGB", (224, 224), color="white")

    classifier = LayoutLMClassifier()
    result = classifier.classify(image=image, ocr_blocks=[])

    assert result is not None
    assert hasattr(result, "confidence")
