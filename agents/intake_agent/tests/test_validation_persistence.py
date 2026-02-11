import pytest
import uuid
from fastapi import HTTPException
from src.services.intake_services.loan_intake_service import LoanIntakeService
from src.models.interfaces.Loan_intake_interfaces import LoanIntakeRequest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_validation_logic_in_exception(db_session: AsyncSession):
    service = LoanIntakeService(db_session)

    request = LoanIntakeRequest(
        request_id=str(uuid.uuid4()),
        callback_url="https://example.com/callback",
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
                "first_name": "123",  # ❌ This will trigger the first Fail-Fast error
                "last_name": "Doe",
                "date_of_birth": "2018-01-01",
                "ssn_last4": "12A",
                "phone_number": "+12345678901",
                "gender": "MALE",
                "email": f"test-{uuid.uuid4()}@test.com",
                "addresses": [],
                "assets": [],
                "liabilities": [],
                "incomes": []
            }
        ]
    )

    # 1. Capture the exception
    with pytest.raises(HTTPException) as excinfo:
        await service.submit_application(request)

    # 2. Verify the Status Code
    assert excinfo.value.status_code == 400
    
    # 3. Verify the Detail (Since logic rolls back, we check the message sent to user)
    # Your code currently sends: raise HTTPException(status_code=400, detail=validation_issues[-1]["message"])
    error_message = excinfo.value.detail
    
    # Based on your service logic, it returns the message of the FIRST failed validation found
    assert "First name" in error_message or "invalid characters" in error_message