from typing import Optional
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

from src.utils.validation.aggregator import validate_applicant
from types import SimpleNamespace
from fastapi import HTTPException
from src.utils.validation.blocking_aggregator import (
    validate_all_applicants_blocking)

from src.models.enums import ApplicantStatus
class LoanIntakeService:
    
    def __init__(
        self, 
        db: AsyncSession, 
        dao: Optional[LoanIntakeDAO] = None, 
        validation_repo: Optional[ValidationRepository] = None
    ):
        self.db = db
        # If no DAO is provided (Prod), create it. If provided (Test), use it.
        self.dao = dao or LoanIntakeDAO(db)
        self.validation_repo = validation_repo or ValidationRepository()

    async def check(self) -> str:
        return "Loan Intake Service is operational."
    
    # async def submit_application(self, request: LoanIntakeRequest) -> LoanIntakeResponse:
    #     try:

    #         validation_summary = validate_all_applicants_blocking(request.applicants)
    #         if not validation_summary.is_valid:
    #             error_content = [
    #                 {"field": err.field, "reason_code": "BLOCKING_ERROR", "message": err.message}
    #                 for err in validation_summary.errors
    #             ]
    #             raise HTTPException(status_code=400, detail=error_content)
    #         # -----------------------------
    #         # 1. Create Loan Application
    #         # -----------------------------
    #         loan = await self.dao.create_loan_application({
    #             "loan_type": request.loan_type,
    #             "credit_type": request.credit_type,
    #             "loan_purpose": request.loan_purpose,
    #             "requested_amount": request.requested_amount,
    #             "requested_term_months": request.requested_term_months,
    #             "preferred_payment_day": request.preferred_payment_day,
    #             "origination_channel": request.origination_channel,
    #             "application_status": ApplicantStatus.SUBMITTED
    #         })

    #         # 🔹 ADDITION: collect validation issues
    #         validation_issues = []

    #         # -----------------------------
    #         # 2. Applicants & Children
    #         # -----------------------------
    #         for applicant in request.applicants:
    #             summary = validate_applicant(applicant)
    #             print(f"Validation summary {summary}")
    #             for res in summary.results:
    #                 print(f"Validation result {res.is_valid}")
    #                 if not res.is_valid:
    #                     repo_result = SimpleNamespace(
    #                         reason_code=SimpleNamespace(value="non_blocking_validation"),
    #                         message=(res.reason or "validation failed")
    #                     )

    #                     await self.validation_repo.save(
    #                         session=self.db,
    #                         application_id=loan.application_id,
    #                         field_name=f"applicant.{res.field}",
    #                         result=repo_result
    #                     )

    #                     validation_issues.append({
    #                         "field": f"applicant.{res.field}",
    #                         "reason_code": repo_result.reason_code.value,
    #                         "message": repo_result.message,
    #                     })
    #                     raise HTTPException(status_code=400, detail=validation_issues)
                    
    #             applicant_row = await self.dao.create_applicant({
    #                 "application_id": loan.application_id,
    #                 "applicant_role": applicant.applicant_role,
    #                 "first_name": applicant.first_name,
    #                 "middle_name": applicant.middle_name,
    #                 "last_name": applicant.last_name,
    #                 "suffix": applicant.suffix,
    #                 "date_of_birth": applicant.date_of_birth,
    #                 "ssn_encrypted": applicant.ssn_no,
    #                 "ssn_last4": applicant.ssn_last4,
    #                 "itin_number": applicant.itin_number,
    #                 "citizenship_status": applicant.citizenship_status,
    #                 "email": applicant.email,
    #                 "phone_number": applicant.phone_number,
    #                 "gender": applicant.gender,
    #             })

    #             # ==================================================
    #             # 🔹 ADDITION: Applicant-level Validations
    #             # ==================================================
    #             validations = [
    #                 ("first_name", validate_first_name(applicant.first_name)),
    #                 ("last_name", validate_last_name(applicant.last_name)),
    #                 ("ssn_last4", validate_ssn_last4(applicant.ssn_last4)),
    #                 ("dob", validate_dob(applicant.date_of_birth)),
    #                 ("email", validate_email(applicant.email)),
    #             ]

    #             for field, result in validations:
    #                 if not result.passed:
    #                     issue = {
    #                         "field": f"applicant.{field}",
    #                         "reason_code": result.reason_code.value, # e.g., "INVALID_FIRST_NAME"
    #                         "message": result.message
    #                     }
    #                     await self.validation_repo.save(
    #                         session=self.db,
    #                         application_id=loan.application_id,
    #                         field_name=f"applicant.{field}",
    #                         result=result
    #                     )
    #                     validation_issues.append(issue)

    #             # -----------------------------
    #             # Addresses
    #             # -----------------------------
    #             for address in applicant.addresses:
    #                 await self.dao.create_address({
    #                     "applicant_id": applicant_row.applicant_id,
    #                     **address.model_dump()
    #                 })

    #                 address_validations = [
    #                     ("line1", validate_address_line(address.address_line1)),
    #                     ("city", validate_city(address.city)),
    #                     ("state", validate_state(address.state)),
    #                     ("zip", validate_zip(address.zip_code)),
    #                 ]

    #                 for field, result in address_validations:
    #                     if not result.passed:
    #                         issue = {
    #                             "field": f"address.{field}",
    #                             "reason_code": result.reason_code.value,
    #                             "message": result.message
    #                         }
    #                         await self.validation_repo.save(
    #                             session=self.db,
    #                             application_id=loan.application_id,
    #                             field_name=f"address.{field}",
    #                             result=result
    #                         )
    #                         validation_issues.append(issue)

    #             # -----------------------------
    #             # Employment (optional)
    #             # -----------------------------
    #             if applicant.employment:
    #                 await self.dao.create_employment({
    #                     "applicant_id": applicant_row.applicant_id,
    #                     **applicant.employment.model_dump()
    #                 })

    #                 employment = applicant.employment
    #                 employment_validations = [
    #                     ("type", validate_employment_type(employment.employment_type)),
    #                     ("employer_name", validate_employer_name(employment.employer_name)),
    #                     ("job_title", validate_job_title(employment.job_title)),
    #                     ("monthly_income", validate_monthly_income(employment.gross_monthly_income)),
    #                 ]

    #                 for field, result in employment_validations:
    #                     if not result.passed:
    #                         issue = {
    #                             "field": f"employment.{field}",
    #                             "reason_code": result.reason_code.value,
    #                             "message": result.message
    #                         }
    #                         await self.validation_repo.save(
    #                             session=self.db,
    #                             application_id=loan.application_id,
    #                             field_name=f"employment.{field}",
    #                             result=result
    #                         )
    #                         validation_issues.append(issue)

    #             # -----------------------------
    #             # Income
    #             # -----------------------------
    #             for income in applicant.incomes:
    #                 await self.dao.create_income({
    #                     "applicant_id": applicant_row.applicant_id,
    #                     **income.model_dump()
    #                 })

    #             # -----------------------------
    #             # Assets
    #             # -----------------------------
    #             for asset in applicant.assets:
    #                 await self.dao.create_asset({
    #                     "applicant_id": applicant_row.applicant_id,
    #                     **asset.model_dump()
    #                 })

    #             # -----------------------------
    #             # Liabilities
    #             # -----------------------------
    #             for liability in applicant.liabilities:
    #                 data = liability.model_dump()
    #                 data["delinquent_flag"] = data.pop("delinquent")

    #                 await self.dao.create_liability({
    #                     "applicant_id": applicant_row.applicant_id,
    #                     **data
    #                 })
    #         if validation_issues:
    #             await self.db.rollback() # Rollback the loan creation
    #             raise HTTPException(
    #                 status_code=400, 
    #                 detail={"success": False, "errors": validation_issues}
    #             )

    #         await self.db.commit()

    #         # 🔹 ADDITION: return validation issues (non-blocking)
    #         return LoanIntakeResponse(
    #             application_id=loan.application_id,
    #             timestamp=datetime.utcnow(),
    #             validation_issues=validation_issues,
    #             validation_summary=validation_summary
    #         )

    #     except SQLAlchemyError:
    #         await self.db.rollback()
    #         raise HTTPException(status_code=500, detail="Database error during loan application submission.")

#   Below is clean code representation of above code--------------------------------------------------

    async def submit_application(self, request: LoanIntakeRequest) -> LoanIntakeResponse:
        try:
            validation_summary = validate_all_applicants_blocking(request.applicants)
            self._ensure_no_blocking_errors(validation_summary)
            loan = await self.dao.create_loan_application(self._map_loan_data(request))

            validation_issues = await self._process_applicants(loan.application_id, request.applicants)

            if validation_issues:
                await self.db.rollback()
                raise HTTPException(status_code=400, detail={"success": False, "errors": validation_issues})
            
            await self.db.commit()
            return self._build_response(loan.application_id, validation_summary, validation_issues)

        except SQLAlchemyError:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Database error during loan application submission.")

    # --- Helper Methods (Levels of Abstraction) ---

    def _ensure_no_blocking_errors(self, summary):
        if not summary.is_valid:
            error_content = [
                {
                    "field": err.field, 
                    # Use the actual reason_code from the error object if it exists, 
                    # otherwise fallback to a generic code.
                    "reason_code": err.reason_code.value if hasattr(err, 'reason_code') and err.reason_code else "VALIDATION_ERROR",
                    "message": err.message
                }
                for err in summary.errors
            ]
            raise HTTPException(status_code=400, detail=error_content)
    async def _process_applicants(self, app_id: str, applicants: list) -> list:
        all_issues = []
        for applicant in applicants:
            # Create applicant and get row
            applicant_row = await self.dao.create_applicant({"application_id": app_id, **self._map_applicant_data(applicant)})
            
            # Process nested entities
            all_issues.extend(await self._validate_and_save_applicant_level(app_id, applicant))
            await self._save_nested_entities(applicant_row.applicant_id, applicant)
        return all_issues

    async def _validate_and_save_applicant_level(self, app_id: str, applicant) -> list:
        issues = []
        validations = [
            ("first_name", validate_first_name(applicant.first_name)),
            ("last_name", validate_last_name(applicant.last_name)),
            ("ssn_last4", validate_ssn_last4(applicant.ssn_last4)),
            ("dob", validate_dob(applicant.date_of_birth)),
            ("email", validate_email(applicant.email)),
        ]
        
        for field, result in validations:
            if not result.passed:
                issue = {"field": f"applicant.{field}", "reason_code": result.reason_code.value, "message": result.message}
                await self.validation_repo.save(session=self.db, application_id=app_id, field_name=f"applicant.{field}", result=result)
                issues.append(issue)
        return issues

    async def _save_nested_entities(self, applicant_id: str, applicant):
        """Orchestrates saving addresses, employment, assets, etc."""
        for addr in applicant.addresses:
            await self.dao.create_address({"applicant_id": applicant_id, **addr.model_dump()})
        
        if applicant.employment:
            await self.dao.create_employment({"applicant_id": applicant_id, **applicant.employment.model_dump()})
        
        for income in applicant.incomes:
            await self.dao.create_income({"applicant_id": applicant_id, **income.model_dump()})
        
        for asset in applicant.assets:
            await self.dao.create_asset({"applicant_id": applicant_id, **asset.model_dump()})
            
        for liability in applicant.liabilities:
            data = liability.model_dump()
            data["delinquent_flag"] = data.pop("delinquent")
            await self.dao.create_liability({"applicant_id": applicant_id, **data})

    def _map_loan_data(self, request):
        return {
            "loan_type": request.loan_type,
            "credit_type": request.credit_type,
            "application_status": ApplicantStatus.SUBMITTED,
            "loan_purpose": request.loan_purpose,
            "requested_amount": request.requested_amount,
            "requested_term_months": request.requested_term_months,
            "preferred_payment_day": request.preferred_payment_day,
            "origination_channel": request.origination_channel

        }

    def _build_response(self, app_id, summary, issues):
        return LoanIntakeResponse(
            application_id=app_id,
            timestamp=datetime.utcnow(),
            validation_issues=issues,
            validation_summary=summary
        )
    
    def _map_applicant_data(self, applicant):
        return {
            "first_name": applicant.first_name,
            "middle_name": applicant.middle_name,
            "last_name": applicant.last_name,
            "suffix": applicant.suffix,
            "ssn_last4": applicant.ssn_last4,
            "date_of_birth": applicant.date_of_birth,
            "ssn_encrypted": applicant.ssn_no,
            "itin_number": applicant.itin_number,
            "citizenship_status": applicant.citizenship_status,
            "email": applicant.email,
            "phone_number": applicant.phone_number,
            "gender": applicant.gender
        }