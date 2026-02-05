import torch
from PIL import Image
from transformers import LayoutLMv3Processor, LayoutLMv3ForSequenceClassification

from src.domain.document_classification.ml.base import DocumentClassifierML
from src.domain.document_classification.classification_result import (
    DocumentClassificationResult,
)
from src.domain.document_classification.document_type import DocumentType


# ⚠️ Must match label order used during training
IDX_TO_DOC_TYPE = {
    0: DocumentType.DRIVERS_LICENSE,
    1: DocumentType.PASSPORT,
    2: DocumentType.SSN_CARD,
    3: DocumentType.W2,
    4: DocumentType.PAYSTUB,
    5: DocumentType.BANK_STATEMENT,
}


class LayoutLMClassifier(DocumentClassifierML):
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

    def _prepare_inputs(self, ocr_blocks, image_size):
        words = []
        boxes = []

        width, height = image_size

        for block in ocr_blocks:
            words.append(block.text)

            x0, y0, x1, y1 = block.bbox
            boxes.append([
                int(1000 * x0 / width),
                int(1000 * y0 / height),
                int(1000 * x1 / width),
                int(1000 * y1 / height),
            ])

        return words, boxes

    def classify(self, image: Image.Image, ocr_blocks):
        if image is None or not ocr_blocks:
            return DocumentClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                method="layoutlm",
            )

        words, boxes = self._prepare_inputs(ocr_blocks, image.size)

        encoding = self.processor(
            image,
            words,
            boxes=boxes,
            return_tensors="pt",
            truncation=True,
        )

        with torch.no_grad():
            outputs = self.model(**encoding)

        probs = torch.softmax(outputs.logits, dim=-1)[0]
        idx = int(torch.argmax(probs).item())

        return DocumentClassificationResult(
            document_type=IDX_TO_DOC_TYPE.get(idx, DocumentType.UNKNOWN),
            confidence=float(probs[idx]),
            method="layoutlm",
        )
