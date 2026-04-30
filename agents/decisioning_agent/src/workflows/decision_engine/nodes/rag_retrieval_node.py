"""
RAG retrieval node — Indian decision graph only.

Strategy: per-node direct retrieval. Each analyzer has its own concern
query (in NODE_CONCERN_QUERIES) targeted at the *config values* it needs
— score band thresholds, lending limits, adjustment factors, etc. —
which live in RBI guidelines + bank policy docs in Qdrant.

For every analyzer node we hit Qdrant once (top-5 from each collection)
and format the result as a prompt-ready POLICY GUIDANCE block. The
analyzer prompts read this block and apply the policy.

The combined deduped set of chunks is also stashed in `rag_pool` so the
final response can show what was retrieved overall.
"""

import logging

from src.core.telemetry import track_node
from src.services.rag_retrieval import (
    NODE_CONCERN_QUERIES,
    format_chunks,
    retrieve_for_node,
)
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState

logger = logging.getLogger(__name__)


@track_node("rag_retrieval_engine")
@audit_node(agent_name="decisioning_agent")
def rag_retrieval_node(state: LoanApplicationState) -> LoanApplicationState:
    rag_context_per_node: dict[str, str] = {}
    seen_ids: set = set()
    deduped_pool: list[dict] = []

    for node_key, concern_query in NODE_CONCERN_QUERIES.items():
        chunks = retrieve_for_node(concern_query, top_k_per_collection=3)
        rag_context_per_node[node_key] = format_chunks(chunks)

        for chunk in chunks:
            chunk_id = chunk.get("id")
            if chunk_id is None or chunk_id in seen_ids:
                continue
            seen_ids.add(chunk_id)
            # Strip dense_vector from the persisted view — keeps the
            # checkpointer payload small and the API response readable.
            deduped_pool.append({k: v for k, v in chunk.items() if k != "dense_vector"})

    populated = sum(1 for v in rag_context_per_node.values() if v)
    logger.info(
        "RAG per-node retrieval complete: deduped_pool=%d chunks, contexts populated for %d/%d nodes",
        len(deduped_pool), populated, len(NODE_CONCERN_QUERIES),
    )

    return {
        "rag_pool": deduped_pool,
        "rag_context_per_node": rag_context_per_node,
    }
