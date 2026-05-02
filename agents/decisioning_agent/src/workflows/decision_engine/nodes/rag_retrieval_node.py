"""
RAG retrieval node — Indian decision graph only.

Two-pass strategy:
  1. Common RBI context — query rbi_guidelines once with a broad India retail
     lending query and store the result in `rbi_common_context`.  All 7 analyzer
     nodes receive this identical block so they share the same regulatory backdrop.

  2. Per-node bank policy — for each analyzer we query only the bank_policies
     collection using its specific NODE_CONCERN_QUERIES entry (score bands,
     adjustment factors, DTI thresholds, etc.) and store the result in
     `rag_context_per_node[node_key]`.

The combined deduped set of all retrieved chunks is stored in `rag_pool` for
audit/explainability.
"""

import logging

from src.core.telemetry import track_node
from src.services.rag_retrieval import (
    NODE_CONCERN_QUERIES,
    format_chunks,
    retrieve_rbi_common,
    retrieve_bank_for_node,
)
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState

logger = logging.getLogger(__name__)


@track_node("rag_retrieval_engine")
@audit_node(agent_name="decisioning_agent")
def rag_retrieval_node(state: LoanApplicationState) -> LoanApplicationState:

    seen_ids: set = set()
    deduped_pool: list[dict] = []

    def _pool_extend(chunks: list[dict]) -> None:
        for chunk in chunks:
            chunk_id = chunk.get("id")
            if chunk_id is None or chunk_id in seen_ids:
                continue
            seen_ids.add(chunk_id)
            deduped_pool.append({k: v for k, v in chunk.items() if k != "dense_vector"})

    # ── Pass 1: Common RBI guidelines (shared by all nodes) ───────────────────
    # top_k=3 → ~3 × 700 chars ≈ 500 tokens injected into every node prompt
    rbi_chunks = retrieve_rbi_common(top_k=3)
    rbi_common_context = format_chunks(rbi_chunks)
    _pool_extend(rbi_chunks)

    logger.info("RBI common context: %d chunks retrieved", len(rbi_chunks))

    # ── Pass 2: Per-node bank policy ──────────────────────────────────────────
    # top_k=1 — the top-1 chunk always scores 0.80-0.90 and is the right section.
    # The second chunk (score ~0.65-0.70) is consistently a different node's section
    # — cross-section noise that confuses the LLM.
    rag_context_per_node: dict[str, str] = {}

    for node_key, concern_query in NODE_CONCERN_QUERIES.items():
        chunks = retrieve_bank_for_node(concern_query, top_k=1)
        rag_context_per_node[node_key] = format_chunks(chunks)
        _pool_extend(chunks)

    populated = sum(1 for v in rag_context_per_node.values() if v)
    logger.info(
        "RAG retrieval complete: deduped_pool=%d chunks, bank contexts populated for %d/%d nodes",
        len(deduped_pool), populated, len(NODE_CONCERN_QUERIES),
    )

    return {
        "rag_pool": deduped_pool,
        "rbi_common_context": rbi_common_context,
        "rag_context_per_node": rag_context_per_node,
    }
