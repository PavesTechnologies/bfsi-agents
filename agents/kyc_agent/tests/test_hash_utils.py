import pytest
from src.utils.hash_utils import generate_payload_hash

def test_generate_payload_hash_stability():
    payload1 = {"name": "John", "age": 30}
    payload2 = {"age": 30, "name": "John"}
    
    hash1 = generate_payload_hash(payload1)
    hash2 = generate_payload_hash(payload2)
    
    assert hash1 == hash2

def test_generate_payload_hash_different():
    payload1 = {"name": "John", "age": 30}
    payload2 = {"name": "Jane", "age": 30}
    
    hash1 = generate_payload_hash(payload1)
    hash2 = generate_payload_hash(payload2)
    
    assert hash1 != hash2

def test_generate_payload_hash_nested_stability():
    payload1 = {"a": {"b": 1, "c": 2}, "d": 3}
    payload2 = {"d": 3, "a": {"c": 2, "b": 1}}
    
    hash1 = generate_payload_hash(payload1)
    hash2 = generate_payload_hash(payload2)
    
    assert hash1 == hash2
