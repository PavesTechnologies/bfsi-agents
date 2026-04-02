from types import SimpleNamespace

import pytest

from src.domain.calculators.behavior import classify_behavior
from src.domain.calculators.exposure import classify_exposure
from src.domain.underwriting_models import UnderwritingRequest
from src.policy.policy_loader import load_policy_config
from src.services.underwriting_service import UnderwritingService


def test_classify_behavior_marks_unacceptable_when_chargeoff_present():
    tradelines = [
        {
            "delinquencies30Days": "01",
            "delinquencies60Days": "00",
            "delinquencies90to180Days": "00",
            "derogCounter": "01",
            "status": "97",
        }
    ]

    result = classify_behavior(tradelines, load_policy_config())

    assert result["chargeoff_history"] is True
    assert result["behavior_risk"] == "UNACCEPTABLE"
    assert result["behavior_score"] == 0.0


def test_classify_exposure_estimates_monthly_obligation_when_payment_missing():
    open_trades = [
        {"balanceAmount": "00012000", "monthlyPaymentAmount": "00000000", "terms": "24"},
        {"balanceAmount": "00003000", "monthlyPaymentAmount": "00000150", "terms": "12"},
    ]

    result = classify_exposure(open_trades)

    assert result["total_existing_debt"] == 15000.0
    assert result["monthly_obligation_estimate"] == 650.0
    assert result["exposure_risk"] == "MODERATE"


class _FakeGraph:
    def __init__(self, final_state):
        self.final_state = final_state
        self.calls = []

    async def ainvoke(self, initial_state, config=None):
        self.calls.append((initial_state, config))
        return self.final_state


class _FakeRepo:
    def __init__(self):
        self.saved = []

    async def get_failed_thread(self, application_id):
        return None

    async def delete_failed_thread(self, application_id):
        self.saved.append(("deleted", application_id))

    async def save_failure(self, application_id, thread_id, error_message):
        self.saved.append(("failed", application_id, thread_id, error_message))


class _FakeIdempotencyRepo:
    def __init__(self):
        self.completed = []

    async def get(self, application_id):
        return None

    async def create(self, application_id, request_hash):
        return SimpleNamespace(application_id=application_id, request_hash=request_hash, status="PROCESSING")

    async def reset_processing(self, application_id, request_hash):
        return None

    async def mark_completed(self, application_id, response_payload):
        self.completed.append((application_id, response_payload))

    async def mark_failed(self, application_id, error_message):
        return None


class _FakeAuditRepo:
    async def save_log(self, **kwargs):
        return None


class _FakeUnderwritingRepo:
    async def save_decision(self, **kwargs):
        return None


@pytest.mark.anyio
async def test_underwriting_service_injects_policy_metadata_into_state():
    final_state = {
        "aggregated_risk_score": 72.0,
        "aggregated_risk_tier": "B",
        "parallel_tasks_completed": [],
        "node_execution_times": {},
        "final_response_payload": {
            "application_id": "APP-456",
            "correlation_id": "REQ-456",
            "policy_version": "v2.0",
            "decision": "APPROVE",
            "risk_tier": "B",
            "risk_score": 72.0,
            "loan_details": {
                "approved_amount": 12000.0,
                "approved_tenure_months": 24,
                "interest_rate": 10.0,
                "disbursement_amount": 11760.0,
                "explanation": "Approved within deterministic policy thresholds.",
            },
        },
    }

    service = UnderwritingService.__new__(UnderwritingService)
    service.db = object()
    service.failed_thread_repo = _FakeRepo()
    service.idempotency_repo = _FakeIdempotencyRepo()
    service.service_audit_repo = _FakeAuditRepo()
    service.underwriting_repo = _FakeUnderwritingRepo()
    service.graph = _FakeGraph(final_state)

    request = UnderwritingRequest(
        application_id="APP-456",
        raw_experian_data={"riskModel": [{"score": 700}]},
        requested_amount=12000.0,
        requested_tenure_months=24,
        monthly_income=25000.0,
    )

    await service.execute_underwriting(request, correlation_id="REQ-456")

    initial_state = service.graph.calls[0][0]
    assert initial_state["policy_metadata"]["policy_version"] == "v2.0"
