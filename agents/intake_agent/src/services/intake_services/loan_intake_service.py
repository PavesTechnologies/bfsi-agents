from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.normalization.application_form import RequestNormalizer
from src.models.interfaces.Loan_intake_interfaces import LoanIntakeRequest, LoanIntakeResponse
from src.repositories.intake_repo.loan_intake_repo import LoanIntakeDAO
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from uuid import uuid4

from src.adapters.vault.source_code.ssn_service import SSNVaultService
from src.adapters.vault.source_code.email_service import EmailVaultService
from src.adapters.vault.source_code.phone_number_service import PhoneNumberVaultService

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

from src.services.idempotency_guard import IdempotencyGuard
from src.repositories.idempotency_repository import IdempotencyRepository
from typing import Optional
from src.models.enums import ApplicantStatus

class LoanIntakeService:
    
    def __init__(self, db: AsyncSession, idempotency: Optional[IdempotencyGuard] = None):
        self.db = db
        self.dao = LoanIntakeDAO(db)
        self.validation_repo = ValidationRepository()
        self.idempotency = idempotency or IdempotencyGuard(IdempotencyRepository(db))
        self.ssn_service = SSNVaultService()
        self.email_service = EmailVaultService()
        self.phone_number_service = PhoneNumberVaultService()

    async def check(self) -> str:
        return "Loan Intake Service is operational."
    
    async def submit_application(self, request: LoanIntakeRequest) -> LoanIntakeResponse:
        
        try:
            async def first_execution():
                # -----------------------------
                # 1. Create Loan Application
                # -----------------------------

                # print(f"Normalizing request: {request}")
                normalized_req = RequestNormalizer.normalize_intake_request(request)
                # print(f"Normalized request: {normalized_req}")
                
                loan = await self.dao.create_loan_application({
                    "loan_type": normalized_req.loan_type,
                    "credit_type": normalized_req.credit_type,
                    "loan_purpose": normalized_req.loan_purpose,
                    "requested_amount": normalized_req.requested_amount,
                    "requested_term_months": normalized_req.requested_term_months,
                    "preferred_payment_day": normalized_req.preferred_payment_day,
                    "origination_channel": normalized_req.origination_channel,
                    "application_status": ApplicantStatus.SUBMITTED
                })

                # 🔹 ADDITION: collect validation issues
                validation_issues = []

                # -----------------------------
                # 2. Applicants & Children
                # -----------------------------
                for applicant in normalized_req.applicants:
                    print(f"Validating applicant {applicant.first_name} {applicant.last_name} with non-blocking validators...")
                    summary = validate_applicant(applicant)
                    print(f"Validation summary for applicant {applicant.first_name} {applicant.last_name}: {summary}")
                    print(f"Validation summary {summary}")
                    for res in summary.results:
                        print(f"Validation result {res.is_valid}")
                        if not res.is_valid:
                            repo_result = SimpleNamespace(
                                reason_code=SimpleNamespace(value="non_blocking_validation"),
                                message=(res.reason or "validation failed")
                            )

                            await self.validation_repo.save(
                                session=self.db,
                                application_id=loan.application_id,
                                field_name=f"applicant.{res.field}",
                                result=repo_result
                            )

                            validation_issues.append({
                                "field": f"applicant.{res.field}",
                                "reason_code": repo_result.reason_code.value,
                                "message": repo_result.message,
                            })
                            # ❌ REMOVED: raise HTTPException(status_code=400, detail=validation_issues[-1]["message"])
                        
                    applicant_row = await self.dao.create_applicant({
                        "application_id": loan.application_id,
                        "applicant_role": applicant.applicant_role,
                        "first_name": applicant.first_name,
                        "middle_name": applicant.middle_name,
                        "last_name": applicant.last_name,
                        "suffix": applicant.suffix,
                        "date_of_birth": applicant.date_of_birth,
                        "ssn_encrypted": self.ssn_service.protect_ssn(applicant.ssn_no),
                        "ssn_last4": applicant.ssn_last4,
                        "itin_number": applicant.itin_number,
                        "citizenship_status": applicant.citizenship_status,
                        "email": self.email_service.protect_email(applicant.email),
                        "phone_number": self.phone_number_service.protect_phone_number(applicant.phone_number),
                        "gender": applicant.gender,
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
                response_payload = {
                    "application_id": str(loan.application_id),
                    "timestamp": datetime.utcnow().isoformat(),
                    "validation_issues": validation_issues,
                    "validation_summary": validation_summary.model_dump() if validation_summary else None
                }

                # Mark completed in idempotency repo
                await IdempotencyRepository(self.db).mark_completed(
                    request_id=request.request_id,
                    response_payload=response_payload
                )

                return response_payload

            # 1. Blocking Validations (Run BEFORE idempotency to avoid caching bad requests)
            validation_summary = validate_all_applicants_blocking(request)
            if not validation_summary.is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=validation_summary.to_http_detail()
                )

            # 2. Execute with Idempotency Guard
            return await self.idempotency.execute(
                request_id=request.request_id,
                app_id=str(request.app_id) if request.app_id else str(uuid4()),
                payload=request.model_dump(mode="json"),
                on_first_execution=first_execution,
            )
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error occurred: {e}")
        
        except RuntimeError:
            raise HTTPException(status_code=409, detail="Request already in progress")
