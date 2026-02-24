from datetime import date
from src.services.identity_service import IdentityService

def test_synthetic_identity_detection(synthetic_fraud_fixture):
    from src.adapters.mock_adapters.mock_experian_adapter import MockExperianAdapter

    vendor_response = MockExperianAdapter().get_credit_report(synthetic_fraud_fixture)

    state = IdentityService.process_ssn_verification(
        synthetic_fraud_fixture, vendor_response
    )

    # Assertions based on Adapter logic (fraud_code "08" / future year)
    assert state["issued_year"] > date.today().year
    assert state["ssn_score"] == 0.72  # 720 / 1000

def test_deceased_identity_detection(deceased_person_fixture):
    """Validates PRD 8.2: Hard Fail signal for deceased records."""
    from src.adapters.mock_adapters.mock_experian_adapter import MockExperianAdapter
    
    adapter = MockExperianAdapter()
    vendor_response = adapter.get_credit_report(deceased_person_fixture)
    
    state = IdentityService.process_ssn_verification(
        deceased_person_fixture, vendor_response
    )
    
    assert state["deceased_flag"] is True
    assert state["ssn_valid"] is True 

def test_perfect_match_validation(perfect_match_fixture):
    """Validates PRD 6.1: Name-DOB-SSN consistency check."""
    from src.adapters.mock_adapters.mock_experian_adapter import MockExperianAdapter
    
    adapter = MockExperianAdapter()
    vendor_response = adapter.get_credit_report(perfect_match_fixture)
    
    state = IdentityService.process_ssn_verification(
        perfect_match_fixture, vendor_response
    )
    
    assert state["name_ssn_match"] is True
    assert state["dob_ssn_match"] is True
    assert state["ssn_score"] == 0.75