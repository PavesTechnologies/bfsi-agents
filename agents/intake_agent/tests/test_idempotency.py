from fastapi.testclient import TestClient
from src.main import app
import pytest


@pytest.fixture
def client():
    return TestClient(app)
def test_idempotent_replay(client):
    payload = {
        "request_id": "11111111-1111-1111-1111-111111111111",
        "app_id": "22222222-2222-2222-2222-222222222222",
        "payload": {"name": "John"},
        "callback_url": "https://example.com/callback"
    }

    r1 = client.post("/v1/intake", json=payload)
    assert r1.status_code == 202

    r2 = client.post("/v1/intake", json=payload)
    assert r2.status_code == 202
