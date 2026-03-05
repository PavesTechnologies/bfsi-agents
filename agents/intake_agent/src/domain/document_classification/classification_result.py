from dataclasses import dataclass
from .document_type import DocumentType

@dataclass(frozen=True)
class DocumentClassificationResult:
    document_type: DocumentType
    confidence: float
    method: str  # rule_based | layoutlm
