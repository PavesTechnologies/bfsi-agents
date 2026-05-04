"""
STAGE 4a: Hybrid embeddings.

Dense (BGE-large) catches semantic meaning; sparse (BM25-style) catches
exact terms — "75 lakhs", "Section 4.2.1", "PMAY". Storing both lets a
hybrid search win on queries where one alone would miss.
"""

import math
from collections import Counter

import numpy as np
from sentence_transformers import SentenceTransformer


class HybridEmbedder:
    """Generates both dense and sparse vectors for a chunk."""

    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5"):
        self.dense_model = SentenceTransformer(model_name)

        # BGE prefixes — these materially improve retrieval quality.
        self.query_prefix = "Represent this sentence for searching relevant passages: "
        self.passage_prefix = "Represent this sentence: "

        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}

    def embed_passage(self, text: str) -> np.ndarray:
        return self.dense_model.encode(
            self.passage_prefix + text,
            normalize_embeddings=True,
        )

    def embed_query(self, text: str) -> np.ndarray:
        return self.dense_model.encode(
            self.query_prefix + text,
            normalize_embeddings=True,
        )

    def sparse_encode(self, text: str) -> dict:
        """
        BM25-flavoured sparse vector. Returns {indices, values} for
        non-zero terms. In production you can swap this for SPLADE or
        Qdrant's native BM25 — same interface.
        """
        tokens = text.lower().split()
        if not tokens:
            return {"indices": [], "values": []}

        tf = Counter(tokens)

        indices: list[int] = []
        values: list[float] = []

        for token, count in tf.items():
            if token not in self.vocab:
                self.vocab[token] = len(self.vocab)

            idx = self.vocab[token]
            weight = (count / len(tokens)) * self.idf.get(token, 1.0)

            indices.append(idx)
            values.append(float(weight))

        return {"indices": indices, "values": values}

    def build_idf(self, all_texts: list[str]) -> None:
        """Pre-compute IDF over the corpus. Call once before encoding."""
        doc_count = len(all_texts)
        if doc_count == 0:
            return

        doc_freq: Counter = Counter()
        for text in all_texts:
            unique_tokens = set(text.lower().split())
            for token in unique_tokens:
                doc_freq[token] += 1

        self.idf = {
            token: math.log(doc_count / (df + 1))
            for token, df in doc_freq.items()
        }
