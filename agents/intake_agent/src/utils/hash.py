import json
import hashlib


def stable_payload_hash(payload: dict) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
def stable_bytes_hash(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()
