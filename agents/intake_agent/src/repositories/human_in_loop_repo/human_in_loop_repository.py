from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List

from src.models.human_in_loop import HumanReview
from src.models.models import LoanApplication
from src.models.models import Applicant
from src.models.enums import HumanDecision, ApplicantStatus


class HumanInLoopDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------
    # Create human review
    # -----------------------------
    async def create_review(
        self,
        application_id: str,
        reviewer_id: str,
        decision: HumanDecision,
        reason_codes: List[str],
        comments: Optional[str],
    ) -> HumanReview:

        review = HumanReview(
            application_id=application_id,
            reviewer_id=reviewer_id,
            decision=decision,
            reason_codes=reason_codes,
            comments=comments,
        )

        self.db.add(review)
        return review

    # -----------------------------
    # Update loan application status
    # -----------------------------
    async def update_application_status(
        self,
        application_id: str,
        status: str,
    ) -> None:

        stmt = (
            update(LoanApplication)
            .where(LoanApplication.application_id == application_id)
            .values(application_status=status)
        )

        await self.db.execute(stmt)

    # -----------------------------
    # Fetch applicants for loan
    # -----------------------------
    async def get_applicants(
        self,
        application_id: str,
    ) -> List[Applicant]:

        stmt = select(Applicant).where(
            Applicant.application_id == application_id
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()
