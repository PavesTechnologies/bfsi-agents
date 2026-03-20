import pytest

from src.models.disbursement_transition import DisbursementTransitionLog
from src.repositories.disbursement_transition_repository import (
    DisbursementTransitionRepository,
)


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        self.commits += 1


@pytest.mark.anyio
async def test_disbursement_transition_repository_persists_transition():
    session = FakeSession()
    repo = DisbursementTransitionRepository(session)

    await repo.save_transition(
        application_id="APP-123",
        correlation_id="REQ-123",
        from_status="VALIDATED",
        to_status="SCHEDULED",
        reason="Repayment schedule generated.",
        transition_metadata={"installment_count": 12},
    )

    assert session.commits == 1
    assert len(session.added) == 1
    assert isinstance(session.added[0], DisbursementTransitionLog)
    assert session.added[0].to_status == "SCHEDULED"
