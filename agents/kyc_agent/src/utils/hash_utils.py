import hashlib
import json
from typing import Any


def generate_payload_hash(payload: dict[str, Any]) -> str:
    """
    Generates a stable SHA-256 hash for a given payload dictionary.
    Keys are sorted to ensure consistency across different orderings.
    """
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
