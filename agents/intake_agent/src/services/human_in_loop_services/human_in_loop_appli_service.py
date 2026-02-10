from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.repositories.human_in_loop_repo.human_in_loop_application_repo import ApplicationGetDAO
from src.models.interfaces.human_in_loop_interface import (
    GetApplicationResponse,
    HumanReviewSummary,
)


class ApplicationGetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = ApplicationGetDAO(db)

    async def get_by_application_id(
        self, application_id: str
    ) -> GetApplicationResponse:

        application = await self.dao.get_application(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        latest_review = await self.dao.get_latest_human_review(application_id)

        return GetApplicationResponse(
            application_id=str(application.application_id),
            application_status=application.application_status,
            latest_human_review=(
                HumanReviewSummary(
                    reviewer_id=latest_review.reviewer_id,
                    decision=latest_review.decision,
                    reason_codes=latest_review.reason_codes,
                    comments=latest_review.comments,
                    created_at=latest_review.created_at,
                )
                if latest_review
                else None
            ),
        )
