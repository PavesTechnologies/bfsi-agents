from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.domain.underwriting_models import UnderwritingRequest
from src.services.underwriting_service import UnderwritingService
from src.utils.hash import stable_payload_hash


class FakeGraph:
    def __init__(self, final_state):
        self.final_state = final_state
        self.calls = []

    async def ainvoke(self, initial_state, config=None):
        self.calls.append((initial_state, config))
        return self.final_state


class FakeFailedThreadRepo:
    def __init__(self, failed_thread=None):
        self.failed_thread = failed_thread
        self.saved = []
        self.deleted = []

    async def get_failed_thread(self, application_id):
        return self.failed_thread

    async def save_failure(self, application_id, thread_id, error_message):
        self.saved.append(
            {
                "application_id": application_id,
                "thread_id": thread_id,
                "error_message": error_message,
            }
        )

    async def delete_failed_thread(self, application_id):
        self.deleted.append(application_id)


class FakeIdempotencyRepo:
    def __init__(self, existing=None):
        self.existing = existing
        self.created = []
        self.reset = []
        self.completed = []
        self.failed = []

    async def get(self, application_id):
        return self.existing

    async def create(self, application_id, request_hash):
        self.created.append((application_id, request_hash))
        self.existing = SimpleNamespace(
            application_id=application_id,
            request_hash=request_hash,
            status="PROCESSING",
            response_payload=None,
        )
        return self.existing

    async def reset_processing(self, application_id, request_hash):
        self.reset.append((application_id, request_hash))

    async def mark_completed(self, application_id, response_payload):
        self.completed.append((application_id, response_payload))

    async def mark_failed(self, application_id, error_message):
        self.failed.append((application_id, error_message))


class FakeUnderwritingRepo:
    def __init__(self):
        self.saved = []

    async def save_decision(self, **kwargs):
        self.saved.append(kwargs)


class FakeServiceAuditRepo:
    def __init__(self):
        self.saved = []

    async def save_log(self, **kwargs):
        self.saved.append(kwargs)


def build_service(final_state, *, existing_record=None, failed_thread=None):
    service = UnderwritingService.__new__(UnderwritingService)
    service.db = object()
    service.failed_thread_repo = FakeFailedThreadRepo(failed_thread=failed_thread)
    service.idempotency_repo = FakeIdempotencyRepo(existing=existing_record)
    service.service_audit_repo = FakeServiceAuditRepo()
    service.underwriting_repo = FakeUnderwritingRepo()
    service.graph = FakeGraph(final_state)
    return service


def build_request(monthly_income=22000.0):
    return UnderwritingRequest(
        application_id="APP-123",
        raw_experian_data={"riskModel": [{"score": 710}]},
        requested_amount=10000.0,
        requested_tenure_months=24,
        monthly_income=monthly_income,
    )


@pytest.mark.anyio
async def test_execute_underwriting_returns_cached_idempotent_response():
    cached_payload = {
        "application_id": "APP-123",
        "decision": "APPROVE",
        "loan_details": {"approved_amount": 10000.0},
    }
    request = build_request()
    existing = SimpleNamespace(
        request_hash=stable_payload_hash(request.model_dump()),
        status="COMPLETED",
        response_payload=cached_payload,
    )
    service = build_service(final_state={}, existing_record=existing)

    result = await service.execute_underwriting(request, correlation_id="REQ-123")

    assert result == cached_payload
    assert service.graph.calls == []
    assert service.service_audit_repo.saved[-1]["response_payload"] == cached_payload


@pytest.mark.anyio
async def test_execute_underwriting_uses_request_income_and_returns_canonical_payload():
    final_payload = {
        "application_id": "APP-123",
        "correlation_id": "REQ-123",
        "decision": "APPROVE",
        "risk_tier": "B",
        "risk_score": 71.2,
        "loan_details": {
            "approved_amount": 10000.0,
            "approved_tenure_months": 24,
            "interest_rate": 10.0,
            "disbursement_amount": 9800.0,
            "explanation": "Approved within policy thresholds.",
        },
    }
    final_state = {
        "aggregated_risk_score": 71.2,
        "aggregated_risk_tier": "B",
        "parallel_tasks_completed": ["income_engine", "underwriting_decision_engine"],
        "node_execution_times": {"income_engine": 0.01},
        "final_response_payload": final_payload,
    }
    service = build_service(final_state=final_state)
    request = build_request(monthly_income=31000.0)

    result = await service.execute_underwriting(request, correlation_id="REQ-123")

    assert result == final_payload
    assert service.graph.calls[0][0]["bank_statement_summary"]["monthly_income"] == 31000.0
    assert service.graph.calls[0][0]["correlation_id"] == "REQ-123"
    assert service.idempotency_repo.completed[-1] == ("APP-123", final_payload)
    assert service.underwriting_repo.saved[-1]["final_decision"] == final_payload
    assert service.service_audit_repo.saved[-1]["status"] == "SUCCESS"


@pytest.mark.anyio
async def test_execute_underwriting_marks_failed_and_audits_when_graph_payload_missing():
    final_state = {
        "aggregated_risk_score": 10.0,
        "aggregated_risk_tier": "F",
        "final_response_payload": {},
    }
    service = build_service(final_state=final_state)
    request = build_request()

    with pytest.raises(HTTPException) as exc:
        await service.execute_underwriting(request, correlation_id="REQ-123")

    assert exc.value.status_code == 500
    assert service.idempotency_repo.failed[-1][0] == "APP-123"
    assert service.failed_thread_repo.saved[-1]["application_id"] == "APP-123"
    assert service.service_audit_repo.saved[-1]["status"] == "FAILURE"
