from src.utils.hash import stable_payload_hash


def test_stable_payload_hash_is_order_independent():
    left = {"application_id": "APP-123", "decision": "APPROVE", "loan_details": {"amount": 1000}}
    right = {"loan_details": {"amount": 1000}, "decision": "APPROVE", "application_id": "APP-123"}

    assert stable_payload_hash(left) == stable_payload_hash(right)
