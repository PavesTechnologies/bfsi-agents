from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.loan_info.loan_query_dao import LoanQueryDAO
from src.models.interfaces.loan_query_response_interface import (
    LoanDetailsResponse,
    ApplicantResponse,
    PgsqlDocumentResponse,
)

class LoanQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = LoanQueryDAO(db)

    async def get_full_loan_details(self, application_id):
        loan = await self.dao.get_loan_by_application_id(application_id)

        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        return LoanDetailsResponse(
            application_id = loan.application_id,
            loan_type = loan.loan_type,
            credits_type = loan.credit_type,
            application_status = loan.application_status,
            requested_amount = loan.requested_amount,
            created_at = loan.created_at,
            credit_type = loan.credit_type,
            loan_purpose = loan.loan_purpose,
            requested_term_months = loan.requested_term_months,
            preferred_payment_day = loan.preferred_payment_day,
            origination_channel = loan.origination_channel,

            # ✅ Explicit mapping
            applicants=[
                ApplicantResponse(
                    applicant_id=a.applicant_id,
                    first_name=a.first_name,
                    last_name=a.last_name,
                    email=a.email,
                    phone_number=a.phone_number,
                    gender=a.gender,
                )
                for a in loan.applicant
            ],

            documents=[
                PgsqlDocumentResponse(
                    id=d.id,
                    document_type=d.document_type,
                    file_name=d.file_name,
                    mime_type=d.mime_type,
                    file_size=d.file_size,
                    uploaded_at=d.uploaded_at,
                    is_low_quality=d.is_low_quality,
                    quality_metadata=d.quality_metadata,
                )
                for d in loan.pgsql_documents
            ],
        )

    async def check(self) -> str:
        return "Loan Query Service is operational."