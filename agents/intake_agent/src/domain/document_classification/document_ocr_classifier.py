from dataclasses import dataclass

from src.domain.ocr.ocr_dispatcher import extract_ocr
from src.domain.document_classification.document_type import DocumentType
from src.domain.document_classification.rules import (
    aadhaar_rules,
    pan_rules,
    voter_id_rules,
    salary_slip_rules,
    form16_rules,
    itr_rules,
    passport_rules,
)

CONFIDENCE_THRESHOLD = 0.70

# Ordered by specificity — more specific patterns first to avoid false positives
_RULE_MAP: list[tuple[DocumentType, object]] = [
    (DocumentType.AADHAAR_CARD, aadhaar_rules),
    (DocumentType.PAN_CARD, pan_rules),
    (DocumentType.VOTER_ID, voter_id_rules),
    (DocumentType.FORM_16, form16_rules),
    (DocumentType.SALARY_SLIP, salary_slip_rules),
    (DocumentType.ITR, itr_rules),
    (DocumentType.PASSPORT, passport_rules),
]


@dataclass
class ClassificationResult:
    doc_type: DocumentType
    confidence: float
    ocr_text: str


def classify_document_from_bytes(file_bytes: bytes, mime_type: str) -> ClassificationResult:
    """
    Run AWS Textract OCR on the file, then score each document type
    using keyword rules. Returns the highest-confidence match above
    CONFIDENCE_THRESHOLD, or DocumentType.UNKNOWN.
    """
    ocr_result = extract_ocr(file_bytes=file_bytes, mime_type=mime_type)
    return _classify_text(ocr_result.full_text)


def _classify_text(text: str) -> ClassificationResult:
    best_type = DocumentType.UNKNOWN
    best_score = 0.0

    for doc_type, rule_module in _RULE_MAP:
        score = rule_module.match(text)
        if score > best_score:
            best_score = score
            best_type = doc_type

    if best_score < CONFIDENCE_THRESHOLD:
        best_type = DocumentType.UNKNOWN

    return ClassificationResult(
        doc_type=best_type,
        confidence=round(best_score, 3),
        ocr_text=text,
    )
