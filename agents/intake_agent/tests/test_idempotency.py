from fastapi.testclient import TestClient
from src.main import app
import pytest

@pytest.fixture
def client():
    # 'with' triggers the lifespan events (DB connection/engine setup)
    with TestClient(app) as c:
        yield c

def test_idempotent_replay(client):
    payload = {
        "request_id": "11111111-1111-1111-1111-111111111111",
        "app_id": "22222222-2222-2222-2222-222222222222",
        "payload": {"name": "John"},
        "callback_url": "https://example.com/callback"
    }

    # First request
    r1 = client.post("/v1/intake", json=payload)
    assert r1.status_code == 202

    # Second request (Now the loop won't be closed prematurely)
    r2 = client.post("/v1/intake", json=payload)
    assert r2.status_code == 202