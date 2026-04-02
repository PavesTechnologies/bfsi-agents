"""Local policy index builder for citation-aware explanations."""

from pathlib import Path

from src.policy.policy_registry import get_active_policy
from src.policy.versioning import build_policy_version_metadata
from src.services.policy_retrieval.policy_chunks import chunk_policy_document


def build_policy_index() -> list[dict]:
    policy = get_active_policy()
    metadata = build_policy_version_metadata(policy)
    docs_dir = Path(__file__).resolve().parents[3] / "policy_docs"
    source_path = docs_dir / policy.policy_citation.default_document_name
    chunks = chunk_policy_document(source_path)

    return [
        {
            **metadata,
            "product": policy.policy_citation.product,
            "source_path": str(source_path),
            "section_id": chunk["section_id"],
            "section_title": chunk["section_title"],
            "content": chunk["content"],
        }
        for chunk in chunks
    ]
