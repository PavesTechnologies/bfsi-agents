import hashlib
import json


def generate_payload_hash(payload: dict) -> str:
    normalized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()
