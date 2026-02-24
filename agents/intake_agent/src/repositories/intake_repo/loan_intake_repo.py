from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.validation.constants import ApplicantStatusEnum
from src.models.models import (
    Address,
    Applicant,
    Asset,
    Employment,
    Income,
    Liability,
    LoanApplication,
)


class LoanIntakeDAO:
    """
    DAO responsible ONLY for database persistence.
    No business rules here.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_loan_application(self, loan_data: dict) -> LoanApplication:
        if isinstance(loan_data.get("application_status"), str):
            loan_data["application_status"] = ApplicantStatusEnum(
                loan_data["application_status"]
            )
        loan = LoanApplication(**loan_data)
        self.db.add(loan)
        await self.db.flush()
        return loan

    async def create_applicant(self, applicant_data: dict) -> Applicant:
        applicant = Applicant(**applicant_data)
        self.db.add(applicant)
        await self.db.flush()
        return applicant

    async def create_address(self, address_data: dict):
        self.db.add(Address(**address_data))

    async def create_employment(self, employment_data: dict):
        self.db.add(Employment(**employment_data))

    async def create_income(self, income_data: dict):
        self.db.add(Income(**income_data))

    async def create_asset(self, asset_data: dict):
        self.db.add(Asset(**asset_data))

    async def create_liability(self, liability_data: dict):
        self.db.add(Liability(**liability_data))

    # async def create_document(self, document_data: dict):
    #     self.db.add(Document(**document_data))
