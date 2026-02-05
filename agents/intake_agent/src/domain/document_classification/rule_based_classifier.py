from src.domain.document_classification.document_type import DocumentType
from src.domain.document_classification.classification_result import (
    DocumentClassificationResult,
)
from src.domain.document_classification.rules import (
    dl_rules,
    passport_rules,
    ssn_rules,
    w2_rules,
    paystub_rules,
    bank_statement_rules,
)


class RuleBasedDocumentClassifier:
    def classify(self, text: str, ocr_blocks=None):
        scores = {
            DocumentType.DRIVERS_LICENSE: dl_rules.match(text, ocr_blocks),
            DocumentType.PASSPORT: passport_rules.match(text, ocr_blocks),
            DocumentType.SSN_CARD: ssn_rules.match(text, ocr_blocks),
            DocumentType.W2: w2_rules.match(text, ocr_blocks),
            DocumentType.PAYSTUB: paystub_rules.match(text, ocr_blocks),
            DocumentType.BANK_STATEMENT: bank_statement_rules.match(text, ocr_blocks),
        }

        best_type, best_score = max(scores.items(), key=lambda x: x[1])

        if best_score < 0.6:
            return DocumentClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=best_score,
                method="rule_based",
            )

        return DocumentClassificationResult(
            document_type=best_type,
            confidence=best_score,
            method="rule_based",
        )
