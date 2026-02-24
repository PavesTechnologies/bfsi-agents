from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.interfaces.human_in_loop_interface import (
    GetApplicationResponse,
    HumanReviewSummary,
)
from src.repositories.human_in_loop_repo.human_in_loop_application_repo import (
    ApplicationGetDAO,
)


class ApplicationGetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = ApplicationGetDAO(db)

    async def get_by_application_id(
        self, application_id: str
    ) -> GetApplicationResponse:
        try:
            application_id_obj = UUID(application_id)

            application = await self.dao.get_application(application_id_obj)
            if not application:
                raise HTTPException(status_code=404, detail="Application not found")

            latest_review = await self.dao.get_latest_human_review(application_id_obj)

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

        except ValueError as e:
            raise HTTPException(
                status_code=422, detail="Invalid application ID format"
            ) from e

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
