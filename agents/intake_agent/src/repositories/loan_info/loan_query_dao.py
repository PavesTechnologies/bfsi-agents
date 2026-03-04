from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.models import LoanApplication
from sqlalchemy.orm import selectinload

class LoanQueryDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_loan_by_application_id(self, application_id):
        stmt = (
            select(LoanApplication)
            .where(LoanApplication.application_id == application_id)
            .options(
                selectinload(LoanApplication.applicant),
                selectinload(LoanApplication.pgsql_documents),
            )
        )

        result = await self.db.execute(stmt)
        return result.scalars().first()
