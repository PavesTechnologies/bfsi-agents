# agents/intake_agent/src/domain/document_classification/orchestrator.py

from typing import Optional

from src.domain.document_classification.document_type import DocumentType
from src.domain.document_classification.rule_based_classifier import (
    RuleBasedDocumentClassifier,
)
from src.domain.document_classification.classification_result import (
    DocumentClassificationResult,
)
from src.domain.ocr.tesseract_ocr import extract_ocr
from src.domain.ocr.pdf_utils import pdf_bytes_to_images


MIN_RULE_CONFIDENCE = 0.6
MIN_ML_CONFIDENCE = 0.7


class DocumentTypeIdentifier:
    """
    Orchestrates document type identification.

    Flow:
    1. OCR (PDF → images → text+blocks OR image → text+blocks)
    2. Rule-based classification
    3. ML fallback (LayoutLM)
    """

    def __init__(self, ml_classifier):
        self.rule_classifier = RuleBasedDocumentClassifier()
        self.ml_classifier = ml_classifier

    def identify(
        self,
        *,
        image=None,
        file_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
    ) -> DocumentClassificationResult:
        """
        Identify document type using:
        Rule-based → ML fallback

        Parameters:
        - image: PIL Image (for image uploads)
        - file_bytes: raw bytes (required for PDFs)
        - mime_type: content type
        """

        # -------------------------
        # OCR extraction
        # -------------------------

        if mime_type == "application/pdf":
            if not file_bytes:
                raise ValueError("file_bytes required for PDF OCR")

            images = pdf_bytes_to_images(file_bytes)
            ocr_results = [extract_ocr(img) for img in images]

            full_text = " ".join(r.full_text for r in ocr_results)
            ocr_blocks = [b for r in ocr_results for b in r.blocks]

        else:
            if image is None:
                raise ValueError("image required for non-PDF OCR")

            ocr_result = extract_ocr(image)
            full_text = ocr_result.full_text
            ocr_blocks = ocr_result.blocks

        # -------------------------
        # Rule-based classification
        # -------------------------

        rule_result = self.rule_classifier.classify(
            full_text,
            ocr_blocks,
        )

        if rule_result.confidence >= MIN_RULE_CONFIDENCE:
            return rule_result

        # -------------------------
        # ML fallback (LayoutLM)
        # -------------------------

        ml_result = self.ml_classifier.classify(
            image=image,
            ocr_blocks=ocr_blocks,
        )

        if ml_result.confidence >= MIN_ML_CONFIDENCE:
            return ml_result

        # -------------------------
        # Final fallback
        # -------------------------

        return DocumentClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=max(rule_result.confidence, ml_result.confidence),
            method="combined",
        )
