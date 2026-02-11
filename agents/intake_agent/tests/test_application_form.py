import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from types import SimpleNamespace

# Adjust imports to match your exact file structure
from src.services.intake_services.loan_intake_service import LoanIntakeService
from src.models.interfaces.Loan_intake_interfaces import LoanIntakeRequest
from src.models.enums import ApplicantStatus
from src.models.interfaces.Loan_intake_interfaces import LoanIntakeResponse
from src.utils.validation.blocking_aggregator import BlockingValidationSummary
from src.utils.validation.blocking_aggregator import BlockingValidationSummary
# --- Fixtures ---

@pytest.fixture
def mock_dao():
    """Mocks the Data Access Object to prevent actual DB calls."""
    dao = MagicMock()
    # Setup return values for create methods to avoid attribute errors
    dao.create_loan_application = AsyncMock(return_value=SimpleNamespace(application_id="loan_123"))
    dao.create_applicant = AsyncMock(return_value=SimpleNamespace(applicant_id="app_456"))
    dao.create_address = AsyncMock()
    dao.create_employment = AsyncMock()
    dao.create_income = AsyncMock()
    dao.create_asset = AsyncMock()
    dao.create_liability = AsyncMock()
    return dao

@pytest.fixture
def mock_db():
    """Mocks the Database Session for Commit/Rollback checks."""
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db

@pytest.fixture
def mock_validation_repo():
    """Mocks the repository that saves validation errors."""
    repo = MagicMock()
    repo.save = AsyncMock()
    return repo

@pytest.fixture
def loan_intake_service(mock_dao, mock_db, mock_validation_repo):
    """Instantiates the service with mocked dependencies."""
    return LoanIntakeService(
        dao=mock_dao,
        db=mock_db,
        validation_repo=mock_validation_repo
    )

@pytest.fixture
def sample_payload():
    return LoanIntakeRequest(
        request_id="82fe4089-ca9d-42bb-976b-bd903e87f151",
        callback_url="http://test.com",
        loan_type="personal",
        credit_type="individual",
        requested_amount=10000.0,
        loan_purpose="PURCHASE",
        requested_term_months=12,
        preferred_payment_day=15,
        origination_channel="ONLINE",
        applicants=[{
            "applicant_role": "primary",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone_number": "1234567890",
            "gender": "MALE",
            "ssn_last4": "1234",
            "date_of_birth": "1990-01-01",
            
            "addresses": [{
                "address_line1": "123 Main St",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62704",
                "address_type": "RESIDENTIAL",    # ADDED
                "country": "USA",                 # ADDED
                "housing_status": "OWN",          # ADDED
                "years_at_address": 2,            # ADDED
                "months_at_address": 6            # ADDED
            }],
            
            "employment": {
                "employment_type": "FULL_TIME",
                "employer_name": "Tech Corp",
                "job_title": "Engineer",
                "gross_monthly_income": 5000.0,
                "employment_status": "CURRENT"    # ADDED
            },
            "incomes": [],
            "assets": [],
            "liabilities": []
        }]
    )

# --- Test Cases ---
@pytest.mark.asyncio
class TestSubmitApplication:

    async def test_submit_application_happy_path(self, loan_intake_service, mock_dao, mock_db, sample_payload):
        """
        Scenario: All validations pass.
        Expectation: Loan created, DB committed, Response returned.
        """

        generated_id = str(uuid.uuid4())
        mock_dao.create_loan_application.return_value = SimpleNamespace(
            application_id=generated_id
        )
        mock_dao.create_applicant.return_value = SimpleNamespace(
            applicant_id=str(uuid.uuid4())
        )
        # 1. Mock External Validators to Pass
        with patch("src.services.intake_services.loan_intake_service.validate_all_applicants_blocking") as mock_blocking, \
             patch("src.services.intake_services.loan_intake_service.validate_applicant") as mock_app_val, \
             patch("src.services.intake_services.loan_intake_service.validate_first_name") as mock_field_val: # Add other specific mocks as needed
            
            # Blocking check passes
            mock_blocking.return_value = BlockingValidationSummary(is_valid=True, errors=[])            
            # Structural check passes
            mock_app_val.return_value = SimpleNamespace(results=[SimpleNamespace(is_valid=True)])
            
            # Field checks pass (Mocking the generic return for all field validators for simplicity)
            mock_field_val.return_value = SimpleNamespace(passed=True)
            
            # We also need to patch the other validators called in the loop (last_name, ssn, etc)
            # For brevity in this example, assume we patch them or they are mocked to return True
            with patch("src.services.intake_services.loan_intake_service.validate_last_name", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_ssn_last4", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_dob", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_email", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_address_line", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_city", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_state", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_zip", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_employment_type", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_employer_name", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_job_title", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_monthly_income", return_value=SimpleNamespace(passed=True)):

                # 2. Act
                response = await loan_intake_service.submit_application(sample_payload)

                # 3. Assert
                mock_dao.create_loan_application.assert_awaited_once()
                mock_dao.create_applicant.assert_awaited_once()
                mock_dao.create_address.assert_awaited_once()
                mock_db.commit.assert_awaited_once()
                assert response.application_id == "loan_123"

    async def test_blocking_validation_failure(self, loan_intake_service, sample_payload, mock_dao):
        """
        Scenario: High-level blocking validation fails (e.g. duplicate applicants).
        Expectation: 400 Error raised immediately. No DB entries created.
        """
        with patch("src.services.intake_services.loan_intake_service.validate_all_applicants_blocking") as mock_blocking:
            
            # Setup failure
            mock_blocking.return_value = SimpleNamespace(
                is_valid=False, 
                errors=[SimpleNamespace(field="applicants", message="Duplicate applicant")]
            )

            with pytest.raises(HTTPException) as exc:
                await loan_intake_service.submit_application(sample_payload)
            
            assert exc.value.status_code == 400
            assert "BLOCKING_ERROR" in str(exc.value.detail)
            
            # Ensure we didn't start creating things
            mock_dao.create_loan_application.assert_not_called()

    async def test_accumulated_validation_failure_rollback(self, loan_intake_service, sample_payload, mock_db, mock_validation_repo):
        """
        Scenario: Blocking passes, but field-level validation (e.g. invalid email) fails.
        Expectation: 
            1. Data is attempted to be inserted.
            2. Validation Repo saves the error.
            3. 400 Error is raised at the END.
            4. DB Rollback is called.
        """
        with patch("src.services.intake_services.loan_intake_service.validate_all_applicants_blocking") as mock_blocking, \
             patch("src.services.intake_services.loan_intake_service.validate_applicant") as mock_app_val, \
             patch("src.services.intake_services.loan_intake_service.validate_email") as mock_email_val:

            # Blocking passes
            mock_blocking.return_value = SimpleNamespace(is_valid=True, errors=[])
            # Structural passes
            mock_app_val.return_value = SimpleNamespace(results=[SimpleNamespace(is_valid=True)])
            
            # Specific field fails (e.g. Email)
            mock_email_val.return_value = SimpleNamespace(
                passed=False, 
                reason_code=SimpleNamespace(value="INVALID_EMAIL"), 
                message="Bad email"
            )

            # Mock other required validators to pass so we isolate the email failure
            with patch("src.services.intake_services.loan_intake_service.validate_first_name", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_last_name", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_ssn_last4", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_dob", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_address_line", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_city", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_state", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_zip", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_employment_type", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_employer_name", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_job_title", return_value=SimpleNamespace(passed=True)), \
                 patch("src.services.intake_services.loan_intake_service.validate_monthly_income", return_value=SimpleNamespace(passed=True)):
            
                with pytest.raises(HTTPException) as exc:
                    await loan_intake_service.submit_application(sample_payload)

                assert exc.value.status_code == 400
                
                # Verify Rollback happened
                mock_db.rollback.assert_awaited_once()
                mock_db.commit.assert_not_called()
                
                # Verify the error was saved to the repo
                mock_validation_repo.save.assert_awaited()
                call_args = mock_validation_repo.save.call_args[1]
                assert call_args['field_name'] == "applicant.email"

    async def test_database_exception_handling(self, loan_intake_service, sample_payload, mock_dao, mock_db):
        """
        Scenario: Database connection dies during applicant creation.
        Expectation: 500 Error raised, DB Rollback called.
        """
        with patch("src.services.intake_services.loan_intake_service.validate_all_applicants_blocking") as mock_blocking:
            mock_blocking.return_value = SimpleNamespace(is_valid=True)
            
            # DAO raises SQLAlchemyError
            mock_dao.create_loan_application.side_effect = SQLAlchemyError("DB Connection Lost")

            with pytest.raises(HTTPException) as exc:
                await loan_intake_service.submit_application(sample_payload)
            
            assert exc.value.status_code == 500
            assert "Database error" in str(exc.value.detail)
            mock_db.rollback.assert_awaited_once()