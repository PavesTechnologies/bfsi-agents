import torch
from transformers import LayoutLMv3Processor, LayoutLMv3ForSequenceClassification

from src.domain.document_classification.document_type import DocumentType
from src.domain.document_classification.classification_result import (
    DocumentClassificationResult,
)

IDX_TO_DOC_TYPE = {
    0: DocumentType.DRIVERS_LICENSE,
    1: DocumentType.PASSPORT,
    2: DocumentType.PAY_STUB,
    3: DocumentType.W2,
}


class LayoutLMClassifier:
    def __init__(self):
        self.processor = LayoutLMv3Processor.from_pretrained(
            "microsoft/layoutlmv3-base",
            apply_ocr=False,
        )
        self.model = LayoutLMv3ForSequenceClassification.from_pretrained(
            "microsoft/layoutlmv3-base",
            num_labels=len(IDX_TO_DOC_TYPE),
        )
        self.model.eval()

    def classify(self, *, file_bytes: bytes, ocr_blocks):
        words = [b.text for b in ocr_blocks]
        boxes = [
            [
                int(b.bbox["left"] * 1000),
                int(b.bbox["top"] * 1000),
                int((b.bbox["left"] + b.bbox["width"]) * 1000),
                int((b.bbox["top"] + b.bbox["height"]) * 1000),
            ]
            for b in ocr_blocks
        ]

        encoding = self.processor(
            images=None,
            text=words,
            boxes=boxes,
            return_tensors="pt",
            truncation=True,
        )

        with torch.no_grad():
            outputs = self.model(**encoding)
            probs = torch.softmax(outputs.logits, dim=1)
            idx = torch.argmax(probs).item()

        return DocumentClassificationResult(
            document_type=IDX_TO_DOC_TYPE[idx],
            confidence=float(probs[0][idx]),
            method="layoutlm",
        )
