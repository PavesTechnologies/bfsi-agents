from src.domain.document_classification.classification_result import (
    DocumentClassificationResult,
)
from src.domain.document_classification.document_type import DocumentType
from src.domain.document_classification.rule_based_classifier import (
    RuleBasedDocumentClassifier,
)
from src.domain.ocr.aws_textract_ocr import extract_ocr_from_bytes

MIN_RULE_CONFIDENCE = 0.6
MIN_ML_CONFIDENCE = 0.7
MIN_VISION_CONFIDENCE = 0.45


def looks_like_id_card(width: int, height: int) -> bool:
    if height == 0:
        return False
    ratio = width / height
    return 1.4 <= ratio <= 1.9


class DocumentTypeIdentifier:
    def __init__(self, ml_classifier, vision_validator):
        self.rule_classifier = RuleBasedDocumentClassifier()
        self.ml_classifier = ml_classifier
        self.vision_validator = vision_validator

    def identify(self, *, file_bytes: bytes, image_size: tuple[int, int]):
        # ---------------- OCR ----------------
        ocr_result = extract_ocr_from_bytes(file_bytes)
        text = ocr_result.full_text
        ocr_blocks = ocr_result.blocks

        # ---------------- RULES ----------------
        rule_result = self.rule_classifier.classify(text, ocr_blocks)

        if rule_result.confidence >= MIN_RULE_CONFIDENCE:
            base_result = rule_result
        else:
            # ---------------- LAYOUTLM ----------------
            ml_result = self.ml_classifier.classify(
                file_bytes=file_bytes,
                ocr_blocks=ocr_blocks,
            )

            base_result = ml_result

        # ---------------- VISION VALIDATION ----------------
        vision_conf = self.vision_validator.validate(file_bytes)

        width, height = image_size
        is_id_shape = looks_like_id_card(width, height)

        # ❗ IMPORTANT: EfficientNet does NOT veto ID cards
        if vision_conf < MIN_VISION_CONFIDENCE and not is_id_shape:
            return DocumentClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=vision_conf,
                method="vision_reject",
            )

        # Boost confidence slightly if vision agrees
        final_conf = min(base_result.confidence + 0.15, 1.0)

        return DocumentClassificationResult(
            document_type=base_result.document_type,
            confidence=final_conf,
            method="combined",
        )
