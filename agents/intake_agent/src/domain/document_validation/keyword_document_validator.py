from typing import Tuple
from src.domain.document_classification.rules import (
    passport_rules,
    itr_rules,
    aadhaar_rules,
    pan_rules,
    voter_id_rules,
    salary_slip_rules,
    form16_rules,
)
from src.domain.document_classification.document_type import DocumentType


class KeywordDocumentValidator:
    """
    Intent-aware document validator.
    Endpoint document type is SOURCE OF TRUTH.
    """

    CONFIDENCE_THRESHOLD = 0.85

    RULE_MAP = {
        DocumentType.PASSPORT: passport_rules,
        DocumentType.ITR: itr_rules,
        DocumentType.AADHAAR_CARD: aadhaar_rules,
        DocumentType.PAN_CARD: pan_rules,
        DocumentType.VOTER_ID: voter_id_rules,
        DocumentType.SALARY_SLIP: salary_slip_rules,
        DocumentType.FORM_16: form16_rules,
    }

    NEGATIVE_KEYWORDS: dict = {}


    @classmethod
    def validate(
        cls,
        *,
        expected_type: DocumentType,
        ocr_text: str,
    ) -> Tuple[bool, float]:
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
