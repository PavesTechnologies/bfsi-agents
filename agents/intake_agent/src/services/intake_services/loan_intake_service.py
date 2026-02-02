from sqlalchemy.ext.asyncio import AsyncSession
from src.models.interfaces.Loan_intake_interfaces import LoanIntakeRequest, LoanIntakeResponse
from src.repositories.intake_repo.loan_intake_repo import LoanIntakeDAO
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# ============================
# 🔹 ADDITIONS: Error Semantics
# ============================
from src.domain.validation.typed_field_validators import (
    validate_first_name,
    validate_last_name,
    validate_ssn_last4,
    validate_dob,
    validate_email,
    validate_address_line,
    validate_city,
    validate_state,
    validate_zip,
    validate_employment_type,
    validate_employer_name,
    validate_job_title,
    validate_monthly_income,
)
from src.repositories.validation_repository import ValidationRepository


class LoanIntakeService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = LoanIntakeDAO(db)

        # 🔹 ADDITION
        self.validation_repo = ValidationRepository()

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

            # 🔹 ADDITION: collect validation issues
            validation_issues = []

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

                # ==================================================
                # 🔹 ADDITION: Applicant-level Validations
                # ==================================================
                validations = [
                    ("first_name", validate_first_name(applicant.first_name)),
                    ("last_name", validate_last_name(applicant.last_name)),
                    ("ssn_last4", validate_ssn_last4(applicant.ssn_last4)),
                    ("dob", validate_dob(applicant.date_of_birth)),
                    ("email", validate_email(applicant.email)),
                ]

                for field, result in validations:
                    if not result.passed:
                        await self.validation_repo.save(
                            session=self.db,
                            application_id=loan.application_id,
                            field_name=f"applicant.{field}",
                            result=result
                        )
                        validation_issues.append({
                            "field": f"applicant.{field}",
                            "reason_code": result.reason_code.value,
                            "message": result.message
                        })

                # -----------------------------
                # Addresses
                # -----------------------------
                for address in applicant.addresses:
                    await self.dao.create_address({
                        "applicant_id": applicant_row.applicant_id,
                        **address.model_dump()
                    })

                    address_validations = [
                        ("line1", validate_address_line(address.address_line1)),
                        ("city", validate_city(address.city)),
                        ("state", validate_state(address.state)),
                        ("zip", validate_zip(address.zip_code)),
                    ]

                    for field, result in address_validations:
                        if not result.passed:
                            await self.validation_repo.save(
                                session=self.db,
                                application_id=loan.application_id,
                                field_name=f"address.{field}",
                                result=result
                            )
                            validation_issues.append({
                                "field": f"address.{field}",
                                "reason_code": result.reason_code.value,
                                "message": result.message
                            })

                # -----------------------------
                # Employment (optional)
                # -----------------------------
                if applicant.employment:
                    await self.dao.create_employment({
                        "applicant_id": applicant_row.applicant_id,
                        **applicant.employment.model_dump()
                    })

                    employment = applicant.employment
                    employment_validations = [
                        ("type", validate_employment_type(employment.employment_type)),
                        ("employer_name", validate_employer_name(employment.employer_name)),
                        ("job_title", validate_job_title(employment.job_title)),
                        ("monthly_income", validate_monthly_income(employment.gross_monthly_income)),
                    ]

                    for field, result in employment_validations:
                        if not result.passed:
                            await self.validation_repo.save(
                                session=self.db,
                                application_id=loan.application_id,
                                field_name=f"employment.{field}",
                                result=result
                            )
                            validation_issues.append({
                                "field": f"employment.{field}",
                                "reason_code": result.reason_code.value,
                                "message": result.message
                            })

                # -----------------------------
                # Income
                # -----------------------------
                for income in applicant.incomes:
                    await self.dao.create_income({
                        "applicant_id": applicant_row.applicant_id,
                        **income.model_dump()
                    })

                # -----------------------------
                # Assets
                # -----------------------------
                for asset in applicant.assets:
                    await self.dao.create_asset({
                        "applicant_id": applicant_row.applicant_id,
                        **asset.model_dump()
                    })

                # -----------------------------
                # Liabilities
                # -----------------------------
                for liability in applicant.liabilities:
                    data = liability.model_dump()
                    data["delinquent_flag"] = data.pop("delinquent")

                    await self.dao.create_liability({
                        "applicant_id": applicant_row.applicant_id,
                        **data
                    })

            await self.db.commit()

            # 🔹 ADDITION: return validation issues (non-blocking)
            return LoanIntakeResponse(
                application_id=loan.application_id,
                timestamp=datetime.utcnow(),
                validation_issues=validation_issues
            )

        except SQLAlchemyError:
            await self.db.rollback()
            raise
