from src.domain.document_classification.rule_based_classifier import (
    RuleBasedDocumentClassifier,
)
from src.domain.document_classification.document_type import DocumentType


def test_w2_rule_detection():
    text = """
    FORM W-2
    Wage and Tax Statement
    Box 1 Wages
    Box 2 Federal income tax withheld
    """

    classifier = RuleBasedDocumentClassifier()
    result = classifier.classify(text)

    assert result.document_type == DocumentType.W2
    assert result.confidence >= 0.6
