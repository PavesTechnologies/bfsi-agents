from abc import ABC, abstractmethod

from ..classification_result import DocumentClassificationResult


class DocumentClassifierML(ABC):
    @abstractmethod
    def classify(self, image, ocr_blocks) -> DocumentClassificationResult:
        pass
