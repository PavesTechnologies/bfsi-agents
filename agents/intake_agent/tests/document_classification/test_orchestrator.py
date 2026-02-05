from src.domain.document_classification.orchestrator import DocumentTypeIdentifier
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


def test_orchestrator_fallback_to_ml():
    identifier = DocumentTypeIdentifier(ml_classifier=MockMLClassifier())

    result = identifier.identify(
        image=None,
        text="random unrelated text",
        ocr_blocks=None,
    )

    assert result.document_type == DocumentType.PASSPORT
    assert result.method == "mock_ml"
