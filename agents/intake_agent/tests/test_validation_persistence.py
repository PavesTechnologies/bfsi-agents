import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.intake_services.loan_intake_service import LoanIntakeService
from src.models.interfaces.Loan_intake_interfaces import LoanIntakeRequest
from src.domain.validation.reason_codes import ValidationReasonCode
from sqlalchemy import text
import uuid
@pytest.mark.asyncio
async def test_validation_reason_is_persisted(db_session: AsyncSession):

    service = LoanIntakeService(db_session)

    request = LoanIntakeRequest(
        loan_type="personal_loan",
        credit_type="individual",
        loan_purpose="medical",
        requested_amount=5000,
        requested_term_months=12,
        preferred_payment_day=10,
        origination_channel="web",
        applicants=[
            {
                "applicant_role": "primary",
                "first_name": "123",  # ❌ invalid
                "last_name": "Doe",
                "date_of_birth": "2018-01-01",  # ❌ underage
                "ssn_last4": "12A",  # ❌ invalid
                "email": f"bad-email-{uuid.uuid4()}@test.com",
                "addresses": [],
                "assets": [],
                "liabilities": [],
                "incomes": []
            }
        ]
    )

    response = await service.submit_application(request)
    rows = await db_session.execute(
    text("""
        SELECT field_name, reason_code
        FROM intake_validation_result
        WHERE application_id = :app_id
    """),
    {"app_id": response.application_id}
)

    results = rows.fetchall()
    reason_codes = {row.reason_code for row in results}

    assert ValidationReasonCode.INVALID_FIRST_NAME.value in reason_codes
    assert ValidationReasonCode.INVALID_SSN_LAST4.value in reason_codes
    assert ValidationReasonCode.AGE_BELOW_MINIMUM.value in reason_codes
