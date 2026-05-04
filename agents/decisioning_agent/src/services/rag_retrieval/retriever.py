"""
Hybrid retrieval against both Qdrant collections (rbi_guidelines + bank_policies).

Returns a unified pool of chunks with their dense vectors so the per-node
re-ranker can compute fresh cosine scores without re-encoding the chunk text.
"""

import logging
from typing import Any, Optional

from qdrant_client.http.exceptions import UnexpectedResponse

from src.services.rag_retrieval.client import (
    BANK_COLLECTION,
    RBI_COLLECTION,
    embed_query,
    get_qdrant,
)

logger = logging.getLogger(__name__)


def _search_collection(
    collection: str,
    query_vector: list[float],
    limit: int,
) -> list[dict[str, Any]]:
    client = get_qdrant()

    try:
        # qdrant-client 1.15+: .search() is removed; use .query_points()
        # with `using="dense"` to target the named vector.
        response = client.query_points(
            collection_name=collection,
            query=query_vector,
            using="dense",
            limit=limit,
            with_payload=True,
            with_vectors=True,
        )
        results = response.points
    except UnexpectedResponse as exc:
        logger.warning("Qdrant search failed for %s: %s", collection, exc)
        return []
    except Exception as exc:  # noqa: BLE001 — defensive against client-side errors
        logger.warning("Qdrant search errored for %s: %s", collection, exc)
        return []

    pool: list[dict[str, Any]] = []
    for hit in results:
        payload = hit.payload or {}
        # `hit.vector` may be a dict ({"dense": [...]}) when with_vectors=True
        # on a named-vector collection, or a list for unnamed.
        dense_vec: Optional[list[float]] = None
        raw_vec = getattr(hit, "vector", None)
        if isinstance(raw_vec, dict):
            dense_vec = raw_vec.get("dense")
        elif isinstance(raw_vec, list):
            dense_vec = raw_vec

        pool.append({
            "id": hit.id,
            "score": float(hit.score),
            "source_collection": collection,
            "text_for_llm": payload.get("text_for_llm") or payload.get("text_for_embedding") or "",
            "breadcrumb": payload.get("breadcrumb", ""),
            "section_number": payload.get("section_number", ""),
            "section_title": payload.get("section_title", ""),
            "chapter": payload.get("chapter", ""),
            "source_document": payload.get("source_document", ""),
            "page_numbers": payload.get("page_numbers") or [],
            "raw_table_markdown": payload.get("raw_table_markdown"),
            "dense_vector": dense_vec,
        })
    return pool


def retrieve_rbi_common(top_k: int = 8) -> list[dict[str, Any]]:
    """
    Retrieve broad RBI regulatory context shared across all analyzer nodes.
    Queries only the rbi_guidelines collection with a general India retail
    lending query so each node gets the same common regulatory backdrop.
    """
    query = (
        "RBI guidelines individual personal loan India CIBIL credit score "
        "income FOIR NPA IRACP public record inquiry debt exposure interest rate "
        "fair lending practices audit explainability"
    )
    query_vector = embed_query(query)
    return _search_collection(RBI_COLLECTION, query_vector, top_k)


def retrieve_bank_for_node(concern_query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Per-node bank policy retrieval — queries only the bank_policies collection
    with the node's concern query to fetch institution-specific thresholds.
    """
    if not concern_query.strip():
        return []
    query_vector = embed_query(concern_query)
    return _search_collection(BANK_COLLECTION, query_vector, top_k)


def retrieve_for_node(concern_query: str, top_k_per_collection: int = 5) -> list[dict[str, Any]]:
    """
    Direct per-node retrieval — encode the node's concern query and pull the
    top_k_per_collection chunks from each collection. Used by rag_retrieval_node
    to build a per-analyzer policy slice without sharing a pool.
    """
    if not concern_query.strip():
        return []

    query_vector = embed_query(concern_query)
    rbi = _search_collection(RBI_COLLECTION, query_vector, top_k_per_collection)
    bank = _search_collection(BANK_COLLECTION, query_vector, top_k_per_collection)
    return rbi + bank


def retrieve_pool(profile_query: str, top_k_per_collection: int = 25) -> list[dict[str, Any]]:
    """
    Run dense retrieval against both collections and return a merged pool.

    The pool is intentionally larger than what any single analyzer needs —
    the per-node re-ranker (reranker.py) picks the relevant top-K from here.
    """
    if not profile_query.strip():
        return []

    query_vector = embed_query(profile_query)

    rbi_pool = _search_collection(RBI_COLLECTION, query_vector, top_k_per_collection)
    bank_pool = _search_collection(BANK_COLLECTION, query_vector, top_k_per_collection)

    pool = rbi_pool + bank_pool
    logger.info(
        "RAG pool assembled: %d chunks (rbi=%d, bank=%d)",
        len(pool), len(rbi_pool), len(bank_pool),
    )
    return pool
