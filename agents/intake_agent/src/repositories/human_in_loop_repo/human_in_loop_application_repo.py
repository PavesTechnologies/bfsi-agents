from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from src.models.models import LoanApplication
from src.models.human_in_loop import HumanReview


class ApplicationGetDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_application(self, application_id: str) -> LoanApplication | None:
        stmt = (
            select(LoanApplication)
            .where(LoanApplication.application_id == application_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_human_review(
        self, application_id: str
    ) -> Optional[HumanReview]:
        stmt = (
            select(HumanReview)
            .where(HumanReview.application_id == application_id)
            .order_by(HumanReview.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
