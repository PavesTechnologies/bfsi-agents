"""
Per-node re-ranking against the shared retrieval pool.

The retriever fetched chunks for a borrower-profile query. Each analyzer
node has a different concern (utilization, DPD, inquiries, etc.) and
re-ranks the same pool against its concern phrase to surface the chunks
that matter for *its* prompt.

Cosine similarity in numpy on already-fetched dense vectors — no extra
BGE encode of chunk text needed, since `with_vectors=True` brought the
chunk vectors back from Qdrant.
"""

import logging
from typing import Any

import numpy as np

from src.services.rag_retrieval.client import embed_query

logger = logging.getLogger(__name__)


_RAG_HEADER = (
    "---------------------------------------\n"
    "RBI / BANK POLICY GUIDANCE\n"
    "(Authoritative excerpts from RBI master directions and internal bank policies. "
    "Use these to align your decision with regulatory guidelines and cite section numbers when applicable.)\n"
    "---------------------------------------"
)


def rerank_for_node(
    pool: list[dict[str, Any]],
    concern_query: str,
    top_k: int = 5,
) -> str:
    """
    Score every chunk in the pool against `concern_query`, take the top_k,
    and format them as a prompt-ready string. Returns "" when the pool is
    empty or no chunk has a usable vector — callers inject this string
    directly into the analyzer prompt.
    """
    if not pool:
        return ""

    concern_vec = np.asarray(embed_query(concern_query), dtype=np.float32)
    # BGE outputs are L2-normalized via normalize_embeddings=True, so dot
    # product == cosine similarity.

    scored: list[tuple[float, dict[str, Any]]] = []
    for chunk in pool:
        vec = chunk.get("dense_vector")
        if vec is None:
            continue
        chunk_vec = np.asarray(vec, dtype=np.float32)
        if chunk_vec.shape != concern_vec.shape:
            continue
        score = float(np.dot(concern_vec, chunk_vec))
        scored.append((score, chunk))

    if not scored:
        return ""

    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:top_k]

    return _format_chunks(top)


def format_chunks(chunks: list[dict[str, Any]]) -> str:
    """
    Public formatter — turns a list of retrieved chunks (already in retrieval
    order, e.g. from retrieve_for_node) into a prompt-ready string with the
    standard POLICY GUIDANCE header.
    """
    if not chunks:
        return ""
    scored: list[tuple[float, dict[str, Any]]] = [
        (float(c.get("score") or 0.0), c) for c in chunks
    ]
    return _format_chunks(scored)


def _format_chunks(scored: list[tuple[float, dict[str, Any]]]) -> str:
    lines: list[str] = [_RAG_HEADER, ""]
    for idx, (score, chunk) in enumerate(scored, start=1):
        source = chunk.get("source_collection", "")
        breadcrumb = chunk.get("breadcrumb", "")
        doc = chunk.get("source_document", "")
        text = (chunk.get("text_for_llm") or "").strip()

        header_bits = [f"[{idx}] source={source}", f"score={score:.3f}"]
        if doc:
            header_bits.append(f"doc={doc}")
        if breadcrumb:
            header_bits.append(f"section={breadcrumb}")
        lines.append(" | ".join(header_bits))
        lines.append(text)
        lines.append("")  # blank line between chunks

    return "\n".join(lines).rstrip()
