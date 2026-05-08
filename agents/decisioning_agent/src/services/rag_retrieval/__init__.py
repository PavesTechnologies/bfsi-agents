"""RAG retrieval module — fetches RBI guidelines from Qdrant.

(Bank-policy retrieval is retained on disk but no longer wired into the
decision graph. The decisioning agent reads bank rules from the bank-admin
DB via `src.services.rules_db`.)
"""
from src.services.rag_retrieval.query_builder import build_profile_query
from src.services.rag_retrieval.reranker import format_chunks, rerank_for_node
from src.services.rag_retrieval.retriever import (
    retrieve_for_node,
    retrieve_pool,
    retrieve_rbi_common,
    retrieve_bank_for_node,
)

__all__ = [
    "build_profile_query",
    "format_chunks",
    "rerank_for_node",
    "retrieve_for_node",
    "retrieve_pool",
    "retrieve_rbi_common",
    "retrieve_bank_for_node",
]
