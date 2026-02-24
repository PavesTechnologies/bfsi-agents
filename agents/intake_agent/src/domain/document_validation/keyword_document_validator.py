from src.domain.document_classification.document_type import DocumentType
from src.domain.document_classification.rules import (
    dl_rules,
    itr_rules,
    passport_rules,
    paystub_rules,
    w2_rules,
)


class KeywordDocumentValidator:
    """
    Intent-aware document validator.
    Endpoint document type is SOURCE OF TRUTH.
    """

    CONFIDENCE_THRESHOLD = 0.85

    RULE_MAP = {
        DocumentType.PAY_STUB: paystub_rules,
        DocumentType.W2: w2_rules,
        DocumentType.DRIVERS_LICENSE: dl_rules,
        DocumentType.PASSPORT: passport_rules,
        DocumentType.ITR: itr_rules,
    }

    NEGATIVE_KEYWORDS = {
        DocumentType.W2: ["PAY PERIOD", "NET PAY"],
        DocumentType.PAY_STUB: ["W-2", "WAGE AND TAX STATEMENT"],
    }

    @classmethod
    def validate(
        cls,
        *,
        expected_type: DocumentType,
        ocr_text: str,
    ) -> tuple[bool, float]:
        if expected_type not in cls.RULE_MAP:
            return False, 0.0

        rule = cls.RULE_MAP[expected_type]
        confidence = rule.match(ocr_text)

        # Negative keyword suppression
        text_u = ocr_text.upper()
        for neg in cls.NEGATIVE_KEYWORDS.get(expected_type, []):
            if neg in text_u:
                return False, 0.0

        return confidence >= cls.CONFIDENCE_THRESHOLD, confidence
