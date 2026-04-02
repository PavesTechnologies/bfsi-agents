from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.human_review_models import (
    UnderwritingHumanReviewRequest,
    UnderwritingHumanReviewResponse,
    UnderwritingHumanReviewSummary,
)
from src.repositories.underwriting_human_review_repository import (
    UnderwritingHumanReviewRepository,
)
from src.repositories.underwriting_repository import UnderwritingRepository


class UnderwritingHumanReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.review_repo = UnderwritingHumanReviewRepository(db)
        self.underwriting_repo = UnderwritingRepository(db)

    async def submit_review(
        self, request: UnderwritingHumanReviewRequest
    ) -> UnderwritingHumanReviewResponse:
        if request.decision not in {"APPROVE", "REJECT", "RETURNED_FOR_DATA"}:
            raise HTTPException(status_code=422, detail="decision must be APPROVE, REJECT, or RETURNED_FOR_DATA")

        existing_decision = await self.underwriting_repo.get_decision_by_application(
            request.application_id
        )
        if existing_decision is None:
            raise HTTPException(
                status_code=404,
                detail=f"No underwriting decision found for application_id {request.application_id}",
            )

        review_status = (
            "RETURNED_FOR_DATA"
            if request.decision == "RETURNED_FOR_DATA"
            else "REVIEW_COMPLETED_APPROVE"
            if request.decision == "APPROVE"
            else "REVIEW_COMPLETED_REJECT"
        )
        review = await self.review_repo.create_review(
            application_id=request.application_id,
            underwriting_decision_id=str(existing_decision.id) if getattr(existing_decision, "id", None) else None,
            reviewer_id=request.reviewer_id,
            decision=request.decision,
            review_status=review_status,
            reason_keys=request.reason_keys,
            comments=request.comments,
            review_packet=request.review_packet,
        )
        await self.underwriting_repo.update_human_review_state(
            application_id=request.application_id,
            review_status=review_status,
            review_outcome=request.decision,
            latest_human_review_id=str(review.id) if getattr(review, "id", None) else None,
        )

        return UnderwritingHumanReviewResponse(
            application_id=review.application_id,
            underwriting_decision_id=review.underwriting_decision_id,
            reviewer_id=review.reviewer_id,
            decision=review.decision,
            review_status=review.review_status,
            reason_keys=list(review.reason_keys),
            comments=review.comments,
            created_at=review.created_at,
        )

    async def get_latest_review(self, application_id: str) -> UnderwritingHumanReviewSummary:
        latest_review = await self.review_repo.get_latest_review(application_id)
        if latest_review is None:
            return UnderwritingHumanReviewSummary(application_id=application_id, latest_review=None)

        return UnderwritingHumanReviewSummary(
            application_id=application_id,
            latest_review=UnderwritingHumanReviewResponse(
                application_id=latest_review.application_id,
                underwriting_decision_id=latest_review.underwriting_decision_id,
                reviewer_id=latest_review.reviewer_id,
                decision=latest_review.decision,
                review_status=latest_review.review_status,
                reason_keys=list(latest_review.reason_keys),
                comments=latest_review.comments,
                created_at=latest_review.created_at,
            ),
        )
