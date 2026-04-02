from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.domain.human_review_models import UnderwritingHumanReviewRequest
from src.services.underwriting_human_review_service import (
    UnderwritingHumanReviewService,
)


class FakeReviewRepo:
    def __init__(self):
        self.created = []
        self.latest = None

    async def create_review(self, **kwargs):
        self.created.append(kwargs)
        return SimpleNamespace(id="review-1", created_at=datetime(2026, 4, 1), **kwargs)

    async def get_latest_review(self, application_id: str):
        return self.latest


class FakeUnderwritingRepo:
    def __init__(self, existing=True):
        self.existing = existing
        self.updated = []

    async def get_decision_by_application(self, application_id: str):
        if not self.existing:
            return None
        return SimpleNamespace(id="decision-1", application_id=application_id, decision="REFER_TO_HUMAN")

    async def update_human_review_state(self, **kwargs):
        self.updated.append(kwargs)
        return SimpleNamespace(**kwargs)


def build_service(existing=True):
    service = UnderwritingHumanReviewService.__new__(UnderwritingHumanReviewService)
    service.db = object()
    service.review_repo = FakeReviewRepo()
    service.underwriting_repo = FakeUnderwritingRepo(existing=existing)
    return service


@pytest.mark.anyio
async def test_submit_review_persists_review_when_underwriting_exists():
    service = build_service(existing=True)
    request = UnderwritingHumanReviewRequest(
        application_id="APP-123",
        reviewer_id="reviewer-1",
        decision="APPROVE",
        reason_keys=["UTILIZATION_HIGH"],
        comments="Looks acceptable after manual review.",
        review_packet={"summary": "review me"},
    )

    response = await service.submit_review(request)

    assert response.application_id == "APP-123"
    assert response.decision == "APPROVE"
    assert response.review_status == "REVIEW_COMPLETED_APPROVE"
    assert service.review_repo.created[0]["review_packet"] == {"summary": "review me"}
    assert service.review_repo.created[0]["underwriting_decision_id"] == "decision-1"
    assert service.underwriting_repo.updated[0]["review_outcome"] == "APPROVE"


@pytest.mark.anyio
async def test_submit_review_raises_when_underwriting_not_found():
    service = build_service(existing=False)
    request = UnderwritingHumanReviewRequest(
        application_id="APP-404",
        reviewer_id="reviewer-1",
        decision="APPROVE",
        reason_keys=["UTILIZATION_HIGH"],
    )

    with pytest.raises(HTTPException) as exc:
        await service.submit_review(request)

    assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_get_latest_review_returns_summary():
    service = build_service(existing=True)
    service.review_repo.latest = SimpleNamespace(
        application_id="APP-123",
        underwriting_decision_id="decision-1",
        reviewer_id="reviewer-1",
        decision="REJECT",
        review_status="REVIEW_COMPLETED_REJECT",
        reason_keys=["DTI_HIGH"],
        comments="Rejected after manual review.",
        created_at=datetime(2026, 4, 1),
    )

    summary = await service.get_latest_review("APP-123")

    assert summary.application_id == "APP-123"
    assert summary.latest_review is not None
    assert summary.latest_review.decision == "REJECT"
    assert summary.latest_review.review_status == "REVIEW_COMPLETED_REJECT"
