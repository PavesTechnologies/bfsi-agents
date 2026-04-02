"""Policy version metadata helpers."""

from src.policy.policy_types import UnderwritingPolicy


def build_policy_version_metadata(policy: UnderwritingPolicy) -> dict:
    return {
        "policy_id": policy.policy_citation.policy_id,
        "policy_version": policy.bank.policy_version,
        "effective_date": policy.bank.last_updated,
        "document_version": policy.metadata.document_version,
        "retrieval_index_version": policy.metadata.retrieval_index_version,
    }
