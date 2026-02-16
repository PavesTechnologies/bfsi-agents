# tests/test_kyc_idempotency.py

import uuid

BASE_PATH = "/kyc/execute"


def build_payload(application_id=None, name="John Doe"):
    return {
        "application_id": application_id or str(uuid.uuid4()),
        "applicant_data": {
            "name": name
        }
    }


def test_happy_path(client):
    payload = build_payload()
    headers = {"X-Idempotency-Key": "test-key-1"}

    response = client.post(BASE_PATH, json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert "kyc_status" in data
    assert "confidence_score" in data


def test_replay_same_payload(client):
    payload = build_payload(application_id="11111111-1111-1111-1111-111111111111")
    headers = {"X-Idempotency-Key": "replay-key"}

    r1 = client.post(BASE_PATH, json=payload, headers=headers)
    assert r1.status_code == 200

    r2 = client.post(BASE_PATH, json=payload, headers=headers)
    assert r2.status_code == 200

    assert r2.json().get("replayed") is True


def test_conflict_same_key_different_payload(client):
    application_id = "22222222-2222-2222-2222-222222222222"
    headers = {"X-Idempotency-Key": "conflict-key"}

    payload1 = build_payload(application_id=application_id, name="Alice")
    payload2 = build_payload(application_id=application_id, name="Bob")

    r1 = client.post(BASE_PATH, json=payload1, headers=headers)
    assert r1.status_code == 200

    r2 = client.post(BASE_PATH, json=payload2, headers=headers)
    assert r2.status_code == 409


def test_version_increment(client):
    application_id = "33333333-3333-3333-3333-333333333333"

    payload = build_payload(application_id=application_id)

    r1 = client.post(
        BASE_PATH,
        json=payload,
        headers={"X-Idempotency-Key": "version-key-1"},
    )
    assert r1.status_code == 200

    r2 = client.post(
        BASE_PATH,
        json=payload,
        headers={"X-Idempotency-Key": "version-key-2"},
    )
    assert r2.status_code == 200

    # Ensure not replay
    assert r2.json().get("replayed") is None


def test_missing_idempotency_header(client):
    payload = build_payload()

    response = client.post(BASE_PATH, json=payload)

    assert response.status_code == 400
