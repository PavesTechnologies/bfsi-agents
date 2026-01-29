
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.interfaces.Loan_intake_interfaces import LoanIntakeRequest, LoanIntakeResponse
from src.repositories.intake_repo.loan_intake_repo import LoanIntakeDAO
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class LoanIntakeService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = LoanIntakeDAO(db)

    async def check(self) -> str:
        return "Loan Intake Service is operational."
    
    async def submit_application(self, request: LoanIntakeRequest) -> LoanIntakeResponse:
        try:
            # -----------------------------
            # 1. Create Loan Application
            # -----------------------------
            loan = await self.dao.create_loan_application({
                "loan_type": request.loan_type,
                "credit_type": request.credit_type,
                "loan_purpose": request.loan_purpose,
                "requested_amount": request.requested_amount,
                "requested_term_months": request.requested_term_months,
                "preferred_payment_day": request.preferred_payment_day,
                "origination_channel": request.origination_channel,
                "application_status": "submitted"
            })

            # -----------------------------
            # 2. Applicants & Children
            # -----------------------------
            for applicant in request.applicants:
                applicant_row = await self.dao.create_applicant({
                    "application_id": loan.application_id,
                    "applicant_role": applicant.applicant_role,
                    "first_name": applicant.first_name,
                    "middle_name": applicant.middle_name,
                    "last_name": applicant.last_name,
                    "suffix": applicant.suffix,
                    "date_of_birth": applicant.date_of_birth,
                    "ssn_last4": applicant.ssn_last4,
                    "itin_number": applicant.itin_number,
                    "citizenship_status": applicant.citizenship_status,
                    "email": applicant.email,
                })

                # Addresses
                for address in applicant.addresses:
                    await self.dao.create_address({
                        "applicant_id": applicant_row.applicant_id,
                        **address.model_dump()
                    })

                # Employment (optional)
                if applicant.employment:
                    await self.dao.create_employment({
                        "applicant_id": applicant_row.applicant_id,
                        **applicant.employment.model_dump()
                    })

                # Income
                for income in applicant.incomes:
                    await self.dao.create_income({
                        "applicant_id": applicant_row.applicant_id,
                        **income.model_dump()
                    })

                # Assets
                for asset in applicant.assets:
                    await self.dao.create_asset({
                        "applicant_id": applicant_row.applicant_id,
                        **asset.model_dump()
                    })

                # Liabilities
                for liability in applicant.liabilities:
                    data = liability.model_dump()
                    data["delinquent_flag"] = data.pop("delinquent")

                    await self.dao.create_liability({
                        "applicant_id": applicant_row.applicant_id,
                        **data
                    })

            # # -----------------------------
            # # 3. Documents
            # # -----------------------------
            # for document in request.documents or []:
            #     await self.dao.create_document({
            #         "application_id": loan.application_id,
            #         **document.model_dump()
            #     })

            await self.db.commit()

            return LoanIntakeResponse(
                application_id=loan.application_id,
                timestamp=datetime.utcnow(),
            )

        except SQLAlchemyError:
            await self.db.rollback()
            raise
