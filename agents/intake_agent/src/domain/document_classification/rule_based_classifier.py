from src.domain.document_classification.classification_result import (
    DocumentClassificationResult,
)
from src.domain.document_classification.document_type import DocumentType
from src.domain.document_classification.rules import (
    dl_rules,
    passport_rules,
    paystub_rules,
    w2_rules,
)


class RuleBasedDocumentClassifier:
    def classify(self, text: str, ocr_blocks=None) -> DocumentClassificationResult:
        scores = {
            DocumentType.DRIVERS_LICENSE: dl_rules.match(text, ocr_blocks),
            DocumentType.PASSPORT: passport_rules.match(text, ocr_blocks),
            DocumentType.PAY_STUB: paystub_rules.match(text, ocr_blocks),
            DocumentType.W2: w2_rules.match(text, ocr_blocks),
        }

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        return DocumentClassificationResult(
            document_type=best_type if best_score > 0 else DocumentType.UNKNOWN,
            confidence=best_score,
            method="rule_based",
        )
