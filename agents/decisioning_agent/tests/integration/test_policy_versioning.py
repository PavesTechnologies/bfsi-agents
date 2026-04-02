import os

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")

from src.policy.policy_registry import get_active_policy
from src.policy.versioning import build_policy_version_metadata


def test_policy_versioning_metadata_is_exposed():
    metadata = build_policy_version_metadata(get_active_policy())

    assert metadata["policy_id"] == "UPL_POLICY"
    assert metadata["policy_version"] == "v2.0"
    assert metadata["retrieval_index_version"] == "retrieval-v1"
