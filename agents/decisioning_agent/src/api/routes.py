"""
API Routes for the Decisioning Agent
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "kyc_agent", "src"))

from fastapi import APIRouter, HTTPException, Depends
from src.domain.underwriting_models import CIBILUnderwritingRequest, UnderwritingRequest
from src.utils.db_session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.underwriting_service import UnderwritingService
from src.services.post_kyc_cibil_service import PostKYCCIBILService
from adapters.mock_adapters.mock_cibil_adapter import MockCIBILAdapter  # type: ignore


router = APIRouter(tags=["Underwriting"])


@router.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "agent": "decisioning_agent"}


@router.post("/underwrite")
async def underwrite(
    request: UnderwritingRequest, db: AsyncSession = Depends(get_db)
):
    """
    Trigger the underwriting decision workflow.

    Accepts applicant financial data and the Experian credit report,
    runs the parallel risk evaluation graph, and returns the final
    decision (APPROVE, COUNTER_OFFER, or DECLINE).
    """
    try:
        service = UnderwritingService(db)
        return await service.execute_underwriting(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/underwrite/cibil")
async def underwrite_cibil(
    request: CIBILUnderwritingRequest, db: AsyncSession = Depends(get_db)
):
    """
    Post-KYC credit decisioning pipeline — Indian Bureau (CIBIL).

    **Workflow:**
    1. Receives the verified PAN from the KYC agent handoff
    2. Calls the CIBIL adapter → generates a full mock credit report
    3. Maps the CIBIL report to the decisioning schema
    4. Fans out to **7 parallel LLM nodes**:
       - Credit Score, Public Record, Revolving Utilization,
         Debt Exposure, Payment Behavior, Inquiry Velocity, Income & DTI
    5. Aggregates risk scores → LLM final decision
    6. Returns **APPROVE / COUNTER_OFFER / DECLINE** with full reasoning

    **PAN-driven test scenarios (use the 4-digit numeric segment):**
    | PAN digits | Scenario             | CIBIL Score |
    |------------|----------------------|-------------|
    | 0001–2499  | Prime borrower       | 780         |
    | 2500–4999  | Good borrower        | 730         |
    | 5000–5999  | High utilization     | 660         |
    | 6000–6999  | Subprime             | 580         |
    | 7000–7499  | Written-off          | 510         |
    | 7500–7999  | New to Credit (NH)   | -1          |
    | 8000–8499  | Suit filed           | 490         |
    | 8500–8999  | Wilful defaulter     | 300         |
    | 9000–9999  | Moderate (default)   | 700         |
    """
    try:
        service = PostKYCCIBILService(db)
        return await service.execute(
            pan=request.pan,
            full_name=request.full_name,
            application_id=request.application_id,
            requested_amount=request.requested_amount,
            requested_tenure_months=request.requested_tenure_months,
            monthly_income=request.monthly_income,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cibil/mock-report")
async def preview_cibil_report(
    pan: str = "ABCDE0001F",
    full_name: str = "Ravi Kumar",
):
    """
    Preview the raw CIBIL mock payload for any PAN — **no database required**.

    Use this to inspect exactly what the MockCIBILAdapter returns before
    it enters the decisioning graph.

    **Change the 4-digit numeric part of the PAN to switch scenarios:**

    | PAN            | Scenario           | CIBIL Score |
    |----------------|--------------------|-------------|
    | ABCDE**0001**F | Prime borrower     | 780         |
    | ABCDE**2500**F | Good borrower      | 730         |
    | ABCDE**5000**F | High utilization   | 660         |
    | ABCDE**6000**F | Subprime           | 580         |
    | ABCDE**7000**F | Written-off        | 510         |
    | ABCDE**7500**F | New to Credit (NH) | -1          |
    | ABCDE**8000**F | Suit filed         | 490         |
    | ABCDE**8500**F | Wilful defaulter   | 300         |
    | ABCDE**9000**F | Moderate           | 700         |
    """
    try:
        adapter = MockCIBILAdapter()
        report = await adapter.get_credit_report({"pan": pan, "full_name": full_name})
        return report.model_dump()
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
