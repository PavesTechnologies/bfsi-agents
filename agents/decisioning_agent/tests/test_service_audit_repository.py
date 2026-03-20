import pytest

from src.models.service_audit import ServiceAuditLog
from src.repositories.service_audit_repository import ServiceAuditRepository


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        self.commits += 1


@pytest.mark.anyio
async def test_service_audit_repository_persists_log_entry():
    session = FakeSession()
    repo = ServiceAuditRepository(session)

    await repo.save_log(
        application_id="APP-123",
        correlation_id="REQ-123",
        agent_name="decisioning_agent",
        operation_name="underwrite",
        request_payload={"amount": 1000},
        response_payload={"decision": "APPROVE"},
        status="SUCCESS",
        error_message=None,
        execution_time_ms=42,
    )

    assert session.commits == 1
    assert len(session.added) == 1
    assert isinstance(session.added[0], ServiceAuditLog)
    assert session.added[0].correlation_id == "REQ-123"
