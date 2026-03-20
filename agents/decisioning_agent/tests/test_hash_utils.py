from src.utils.hash import stable_payload_hash


def test_stable_payload_hash_is_order_independent():
    left = {"application_id": "APP-123", "amount": 1000, "nested": {"a": 1, "b": 2}}
    right = {"nested": {"b": 2, "a": 1}, "amount": 1000, "application_id": "APP-123"}

    assert stable_payload_hash(left) == stable_payload_hash(right)
