"""
RBI retrieval node — Indian decision graph only.

Single pass: query the rbi_guidelines Qdrant collection once with a broad
India retail-lending query. The result is stored in `rbi_common_context` and
shared by all 7 analyzer nodes as their regulatory backdrop.

Bank-specific policy (score bands, DTI thresholds, adjustment factors, etc.)
no longer comes from RAG — `rules_loader_node` reads it from the bank-admin
DB and writes both `rules_per_node` (structured) and `rag_context_per_node`
(formatted text) into state.
"""

import logging

from src.core.telemetry import track_node
from src.services.rag_retrieval import format_chunks, retrieve_rbi_common
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState

logger = logging.getLogger(__name__)


@track_node("rag_retrieval_engine")
@audit_node(agent_name="decisioning_agent")
def rag_retrieval_node(state: LoanApplicationState) -> LoanApplicationState:
    # top_k=3 → ~3 × 700 chars ≈ 500 tokens injected into every node prompt
    rbi_chunks = retrieve_rbi_common(top_k=3)
    rbi_common_context = format_chunks(rbi_chunks)

    deduped_pool: list[dict] = [
        {k: v for k, v in chunk.items() if k != "dense_vector"}
        for chunk in rbi_chunks
    ]

    logger.info("RBI common context: %d chunks retrieved", len(rbi_chunks))

    return {
        "rag_pool": deduped_pool,
        "rbi_common_context": rbi_common_context,
    }
