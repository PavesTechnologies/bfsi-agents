from src.domain.document_classification.orchestrator import DocumentTypeIdentifier
import src.domain.document_classification.orchestrator as orchestrator_mod
from src.domain.document_classification.document_type import DocumentType
from src.domain.document_classification.classification_result import (
    DocumentClassificationResult
)


class MockMLClassifier:
    def classify(self, image, ocr_blocks):
        return DocumentClassificationResult(
            document_type=DocumentType.PASSPORT,
            confidence=0.9,
            method="mock_ml",
        )


class MockVisionValidator:
    def validate(self, file_bytes: bytes) -> float:
        return 1.0


def test_orchestrator_fallback_to_ml():
    # stub OCR to avoid AWS call
    orchestrator_mod.extract_ocr_from_bytes = lambda b: type("R", (), {"full_text": "random unrelated text", "blocks": []})()

    identifier = DocumentTypeIdentifier(ml_classifier=MockMLClassifier(), vision_validator=MockVisionValidator())

    result = identifier.identify(
        file_bytes=b"",
        image_size=(1000, 2000),
    )

    assert result.document_type == DocumentType.PASSPORT
    assert result.method == "mock_ml"
