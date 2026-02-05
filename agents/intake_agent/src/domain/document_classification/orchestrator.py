# agents/intake_agent/src/domain/document_classification/orchestrator.py

from typing import Optional

from src.domain.document_classification.document_type import DocumentType
from src.domain.document_classification.rule_based_classifier import (
    RuleBasedDocumentClassifier,
)
from src.domain.document_classification.classification_result import (
    DocumentClassificationResult,
)
from src.domain.ocr.ocr_dispatcher import extract_ocr
from src.domain.ocr.pdf_utils import pdf_bytes_to_images


MIN_RULE_CONFIDENCE = 0.6
MIN_ML_CONFIDENCE = 0.7


class DocumentTypeIdentifier:
    def __init__(self, ml_classifier):
        self.rule_classifier = RuleBasedDocumentClassifier()
        self.ml_classifier = ml_classifier

    def identify(self, file_bytes: bytes, mime_type: str):
        ocr_result = extract_ocr(file_bytes, mime_type)

        text = ocr_result.full_text
        ocr_blocks = ocr_result.blocks

        rule_result = self.rule_classifier.classify(text, ocr_blocks)
        if rule_result.confidence >= MIN_RULE_CONFIDENCE:
            return rule_result

        ml_result = self.ml_classifier.classify(ocr_blocks)
        if ml_result.confidence >= MIN_ML_CONFIDENCE:
            return ml_result

        return DocumentClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=max(rule_result.confidence, ml_result.confidence),
            method="combined",
        )
