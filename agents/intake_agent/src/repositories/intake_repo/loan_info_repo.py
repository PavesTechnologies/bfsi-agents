from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import LoanApplication


class LoanInfoDAO:
    """
    DAO responsible ONLY for database persistence.
    No business rules here.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_loan_application_by_id(self, application_id: str) -> LoanApplication:
        result = await self.db.execute(
            select(LoanApplication).where(
                LoanApplication.application_id == application_id
            )
        )
        return result.scalars().first() if result else None
