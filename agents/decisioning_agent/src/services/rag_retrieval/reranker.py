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


# Max characters per chunk — large enough to fit all threshold definitions
# (4 bands × ~80 chars + limits + weights ≈ 1200 chars, ~300 tokens).
_CHUNK_MAX_CHARS = 1500


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
    """
    Emit only the essential policy text — no scores, no source paths, no
    collection names. Each chunk's text_for_llm already starts with a
    [Section: ...] breadcrumb so the LLM knows the context. Text is capped
    at _CHUNK_MAX_CHARS to keep token count predictable.
    """
    parts: list[str] = []
    for _score, chunk in scored:
        text = (chunk.get("text_for_llm") or "").strip()
        if not text:
            continue
        if len(text) > _CHUNK_MAX_CHARS:
            text = text[:_CHUNK_MAX_CHARS].rsplit(" ", 1)[0] + "..."
        parts.append(text)

    return "\n\n".join(parts)
