from src.services.pipeline_service import PipelineService
from src.store.pipeline_state_store import get_state, save_state


def test_normalize_underwriting_response_approve_shape():
    service = PipelineService()

    normalized = service._normalize_underwriting_response(
        {
            "application_id": "app-1",
            "decision": "APPROVE",
            "loan_details": {
                "approved_amount": 100000.0,
                "approved_tenure_months": 36,
                "interest_rate": 10.5,
                "disbursement_amount": 99000.0,
                "explanation": "Approved loan terms",
            },
        }
    )

    assert normalized["approved_amount"] == 100000.0
    assert normalized["processing_fee"] == 1000.0
    assert normalized["monthly_emi"] > 0

    import asyncio

    asyncio.run(service.close())


def test_cancel_pending_application_clears_state():
    service = PipelineService()
    save_state("app-2", {"phase": "AWAITING_APPROVAL_CONFIRMATION"})

    response = service.cancel_pending_application("app-2")

    assert response == {"status": "CANCELLED_BY_USER", "application_id": "app-2"}
    assert get_state("app-2") is None

    import asyncio

    asyncio.run(service.close())
