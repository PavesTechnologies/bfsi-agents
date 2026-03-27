"""
Tests for /review-queue/* endpoints.

The orchestrator HTTP call inside the decide endpoint is mocked so that
these tests do not need the orchestrator service running.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


def _mock_orchestrator_ok():
    """Return a mock httpx Response with is_success=True."""
    mock_resp = MagicMock()
    mock_resp.is_success = True
    return mock_resp


def _mock_orchestrator_fail():
    mock_resp = MagicMock()
    mock_resp.is_success = False
    return mock_resp


def _patch_orchestrator(return_value=None):
    """
    Patch the httpx.AsyncClient context manager inside review_queue router.
    Usage:  with _patch_orchestrator(_mock_orchestrator_ok()):
    """
    if return_value is None:
        return_value = _mock_orchestrator_ok()

    mock_instance = AsyncMock()
    mock_instance.post = AsyncMock(return_value=return_value)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    return patch("src.routers.review_queue.httpx.AsyncClient", return_value=mock_cm)


# ---------------------------------------------------------------------------
# List /review-queue
# ---------------------------------------------------------------------------

class TestListReviewQueue:
    def test_requires_auth(self, client: TestClient):
        resp = client.get("/review-queue")
        assert resp.status_code == 401

    def test_returns_paginated_response(
        self, client: TestClient, auth_headers, queue_entry
    ):
        resp = client.get("/review-queue", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_pagination_params(self, client: TestClient, auth_headers):
        resp = client.get(
            "/review-queue?page=1&page_size=3", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert len(data["items"]) <= 3

    def test_filter_by_status_pending(
        self, client: TestClient, auth_headers, queue_entry
    ):
        resp = client.get(
            "/review-queue?status=PENDING", headers=auth_headers
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "PENDING"

    def test_filter_by_ai_decision(
        self, client: TestClient, auth_headers, queue_entry
    ):
        resp = client.get(
            "/review-queue?ai_decision=APPROVE", headers=auth_headers
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["ai_decision"] == "APPROVE"

    def test_created_entry_appears_in_list(
        self, client: TestClient, auth_headers, queue_entry
    ):
        resp = client.get("/review-queue?status=PENDING", headers=auth_headers)
        assert resp.status_code == 200
        ids = [i["application_id"] for i in resp.json()["items"]]
        assert queue_entry["application_id"] in ids

    def test_counter_offer_entry_in_list(
        self, client: TestClient, auth_headers, counter_offer_queue_entry
    ):
        resp = client.get(
            "/review-queue?ai_decision=COUNTER_OFFER", headers=auth_headers
        )
        assert resp.status_code == 200
        ids = [i["application_id"] for i in resp.json()["items"]]
        assert counter_offer_queue_entry["application_id"] in ids


# ---------------------------------------------------------------------------
# GET /review-queue/{id}
# ---------------------------------------------------------------------------

class TestGetQueueItem:
    def test_get_by_id_success(
        self, client: TestClient, auth_headers, queue_entry
    ):
        resp = client.get(
            f"/review-queue/{queue_entry['queue_id']}", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == queue_entry["queue_id"]
        assert data["application_id"] == queue_entry["application_id"]
        assert data["status"] == "PENDING"
        assert data["ai_decision"] == "APPROVE"
        assert data["ai_risk_tier"] == "A"
        assert abs(data["ai_risk_score"] - 88.5) < 0.01
        assert abs(data["ai_suggested_amount"] - 50000.0) < 0.01

    def test_get_not_found(self, client: TestClient, auth_headers):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/review-queue/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_requires_auth(self, client: TestClient, queue_entry):
        resp = client.get(f"/review-queue/{queue_entry['queue_id']}")
        assert resp.status_code == 401

    def test_counter_offer_jsonb_fields_present(
        self, client: TestClient, auth_headers, counter_offer_queue_entry
    ):
        resp = client.get(
            f"/review-queue/{counter_offer_queue_entry['queue_id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ai_decision"] == "COUNTER_OFFER"
        assert data["ai_counter_options"] is not None
        opts = data["ai_counter_options"]["generated_options"]
        assert len(opts) == 1
        assert opts[0]["offer_id"] == "OPT_1"


# ---------------------------------------------------------------------------
# POST /review-queue/{id}/assign
# ---------------------------------------------------------------------------

class TestAssignQueueItem:
    def test_assign_success(
        self, client: TestClient, auth_headers, queue_entry
    ):
        resp = client.post(
            f"/review-queue/{queue_entry['queue_id']}/assign",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ASSIGNED"
        assert data["assigned_to"] is not None
        assert data["assignee_name"] == "System Administrator"
        assert data["assigned_at"] is not None

    def test_assign_updates_status_in_db(
        self, client: TestClient, auth_headers, queue_entry
    ):
        # Assign
        client.post(
            f"/review-queue/{queue_entry['queue_id']}/assign", headers=auth_headers
        )
        # Fetch and verify
        resp = client.get(
            f"/review-queue/{queue_entry['queue_id']}", headers=auth_headers
        )
        assert resp.json()["status"] == "ASSIGNED"

    def test_assign_already_assigned_still_ok(
        self, client: TestClient, auth_headers, queue_entry
    ):
        """Re-assigning an ASSIGNED item to the same user is allowed."""
        client.post(
            f"/review-queue/{queue_entry['queue_id']}/assign", headers=auth_headers
        )
        resp = client.post(
            f"/review-queue/{queue_entry['queue_id']}/assign", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_assign_not_found(self, client: TestClient, auth_headers):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/review-queue/{fake_id}/assign", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_assign_requires_auth(self, client: TestClient, queue_entry):
        resp = client.post(f"/review-queue/{queue_entry['queue_id']}/assign")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /review-queue/{id}/decide
# ---------------------------------------------------------------------------

class TestDecideQueueItem:
    def test_decide_reject_records_decision(
        self, client: TestClient, auth_headers, queue_entry
    ):
        with _patch_orchestrator(_mock_orchestrator_ok()):
            resp = client.post(
                f"/review-queue/{queue_entry['queue_id']}/decide",
                headers=auth_headers,
                json={"decision": "REJECTED", "notes": "Insufficient income"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "REJECTED"
        assert data["status"] == "REJECTED"
        assert data["queue_id"] == queue_entry["queue_id"]
        assert data["orchestrator_notified"] is True

    def test_decide_approve_calls_orchestrator(
        self, client: TestClient, auth_headers, queue_entry
    ):
        with _patch_orchestrator(_mock_orchestrator_ok()):
            resp = client.post(
                f"/review-queue/{queue_entry['queue_id']}/decide",
                headers=auth_headers,
                json={"decision": "APPROVED"},
            )
        assert resp.status_code == 200
        assert resp.json()["decision"] == "APPROVED"
        assert resp.json()["orchestrator_notified"] is True

    def test_decide_override_with_custom_terms(
        self, client: TestClient, auth_headers, queue_entry
    ):
        with _patch_orchestrator(_mock_orchestrator_ok()):
            resp = client.post(
                f"/review-queue/{queue_entry['queue_id']}/decide",
                headers=auth_headers,
                json={
                    "decision": "OVERRIDDEN",
                    "override_amount": 40000.0,
                    "override_rate": 8.5,
                    "override_tenure": 48,
                    "notes": "Adjusted terms per policy",
                },
            )
        assert resp.status_code == 200
        assert resp.json()["decision"] == "OVERRIDDEN"

    def test_decide_orchestrator_down_still_records(
        self, client: TestClient, auth_headers, queue_entry
    ):
        """Even if orchestrator is unreachable, the decision is recorded locally."""
        with _patch_orchestrator(_mock_orchestrator_fail()):
            resp = client.post(
                f"/review-queue/{queue_entry['queue_id']}/decide",
                headers=auth_headers,
                json={"decision": "REJECTED", "notes": "test"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "REJECTED"
        assert data["orchestrator_notified"] is False  # notified=False but still 200

    def test_decide_invalid_decision_value(
        self, client: TestClient, auth_headers, queue_entry
    ):
        resp = client.post(
            f"/review-queue/{queue_entry['queue_id']}/decide",
            headers=auth_headers,
            json={"decision": "BANANA"},
        )
        assert resp.status_code == 403

    def test_decide_not_found(self, client: TestClient, auth_headers):
        fake_id = str(uuid.uuid4())
        with _patch_orchestrator():
            resp = client.post(
                f"/review-queue/{fake_id}/decide",
                headers=auth_headers,
                json={"decision": "REJECTED"},
            )
        assert resp.status_code == 404

    def test_decide_requires_auth(self, client: TestClient, queue_entry):
        resp = client.post(
            f"/review-queue/{queue_entry['queue_id']}/decide",
            json={"decision": "REJECTED"},
        )
        assert resp.status_code == 401

    def test_redecide_rejected_item_returns_403(
        self, client: TestClient, auth_headers, queue_entry
    ):
        """Once an item is decided, a second decide call must be rejected."""
        with _patch_orchestrator(_mock_orchestrator_ok()):
            client.post(
                f"/review-queue/{queue_entry['queue_id']}/decide",
                headers=auth_headers,
                json={"decision": "REJECTED"},
            )
        with _patch_orchestrator(_mock_orchestrator_ok()):
            resp = client.post(
                f"/review-queue/{queue_entry['queue_id']}/decide",
                headers=auth_headers,
                json={"decision": "APPROVED"},
            )
        assert resp.status_code == 403
        assert "already decided" in resp.json()["detail"].lower()

    def test_item_status_updated_after_decide(
        self, client: TestClient, auth_headers, queue_entry
    ):
        with _patch_orchestrator(_mock_orchestrator_ok()):
            client.post(
                f"/review-queue/{queue_entry['queue_id']}/decide",
                headers=auth_headers,
                json={"decision": "APPROVED"},
            )
        resp = client.get(
            f"/review-queue/{queue_entry['queue_id']}", headers=auth_headers
        )
        data = resp.json()
        assert data["status"] == "APPROVED"
        assert data["decided_at"] is not None

    def test_cannot_assign_after_decide(
        self, client: TestClient, auth_headers, queue_entry
    ):
        """Assigning a decided item should fail."""
        with _patch_orchestrator(_mock_orchestrator_ok()):
            client.post(
                f"/review-queue/{queue_entry['queue_id']}/decide",
                headers=auth_headers,
                json={"decision": "REJECTED"},
            )
        resp = client.post(
            f"/review-queue/{queue_entry['queue_id']}/assign", headers=auth_headers
        )
        assert resp.status_code == 403
