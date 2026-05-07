"""
HITL Pipeline API — bank-admin-service

Bank-employee endpoints for reviewing applications and finalising credit decisions.
Internal (no-auth) endpoints receive callbacks from the orchestrator to update state.
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, require_permission
from src.core.permissions import Permission
from src.models.loan_application import PipelineStatus
from src.schemas.loan_application import (
    AnalyzerSelectionRequest,
    BankDecisionRequest,
    DecisioningResultPatch,
    DisbursementPatch,
    LoanApplicationCreate,
    LoanApplicationDetail,
    LoanApplicationListResponse,
    SignaturePatch,
)
from src.services.audit_service import AuditService
from src.services.loan_application_service import LoanApplicationService
from src.services.orchestrator_client import OrchestratorClient
from src.utils.finance import emi_from_application

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

_viewer = require_permission(Permission.VIEW_APPLICATIONS)
_approver = require_permission(Permission.APPROVE_LOAN)


# ── Orchestrator callbacks (no JWT — internal network only) ──────────────────

@router.post("/applications", status_code=201)
async def create_application(
    payload: LoanApplicationCreate,
    db: AsyncSession = Depends(get_db),
):
    app = await LoanApplicationService(db).create(payload)
    return {"id": str(app.id), "pipeline_status": app.pipeline_status}


@router.patch("/applications/{app_id}/decisioning-result")
async def patch_decisioning_result(
    app_id: str,
    payload: DecisioningResultPatch,
    db: AsyncSession = Depends(get_db),
):
    app = await LoanApplicationService(db).save_decisioning_result(app_id, payload)
    return {"id": str(app.id), "pipeline_status": app.pipeline_status}


@router.patch("/applications/by-external/{external_id}/awaiting-signature")
async def set_awaiting_signature(external_id: str, db: AsyncSession = Depends(get_db)):
    app = await LoanApplicationService(db).set_awaiting_signature(external_id)
    return {"pipeline_status": app.pipeline_status}


@router.patch("/applications/by-external/{external_id}/cancelled")
async def set_cancelled(external_id: str, db: AsyncSession = Depends(get_db)):
    app = await LoanApplicationService(db).set_cancelled(external_id)
    return {"pipeline_status": app.pipeline_status}


@router.patch("/applications/by-external/{external_id}/signature")
async def save_signature(
    external_id: str,
    payload: SignaturePatch,
    db: AsyncSession = Depends(get_db),
):
    app = await LoanApplicationService(db).save_signature(external_id, payload)
    return {"pipeline_status": app.pipeline_status}


@router.patch("/applications/by-external/{external_id}/disbursement")
async def save_disbursement(
    external_id: str,
    payload: DisbursementPatch,
    db: AsyncSession = Depends(get_db),
):
    app = await LoanApplicationService(db).save_disbursement(external_id, payload)
    return {"pipeline_status": app.pipeline_status}


# ── Bank-employee endpoints (JWT required) ───────────────────────────────────

@router.get("/applications", response_model=LoanApplicationListResponse)
async def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await LoanApplicationService(db).list(page, page_size, status)


@router.get("/applications/{app_id}", response_model=LoanApplicationDetail)
async def get_application(
    app_id: str,
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    app = await LoanApplicationService(db).get_by_id(app_id)
    return LoanApplicationDetail.model_validate(app)


@router.patch("/applications/{app_id}/analyzers")
async def save_analyzer_selection(
    app_id: str,
    payload: AnalyzerSelectionRequest,
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    service = LoanApplicationService(db)
    app = await service.save_analyzer_selection(app_id, payload, current_user["user_id"])
    await AuditService(db).log(
        "ANALYZERS_SELECTED",
        user_id=current_user["user_id"],
        resource_type="loan_application",
        resource_id=app_id,
        after={"active_analyzers": payload.active_analyzers},
    )
    return {"pipeline_status": app.pipeline_status, "active_analyzers": app.active_analyzers}


@router.post("/applications/{app_id}/run-decisioning", status_code=202)
async def run_decisioning(
    app_id: str,
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers decisioning via the orchestrator and returns 202 immediately.
    The orchestrator will PATCH /applications/{app_id}/decisioning-result when done.
    """
    service = LoanApplicationService(db)
    app = await service.get_by_id(app_id)

    if app.pipeline_status != PipelineStatus.AWAITING_BANK_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot run decisioning from status: {app.pipeline_status}",
        )

    await service.set_decisioning_in_progress(app_id)

    # Commit before firing the async task so the status change is visible
    await db.commit()

    asyncio.create_task(
        OrchestratorClient().trigger_decisioning(
            app.external_application_id, app.active_analyzers
        )
    )

    await AuditService(db).log(
        "DECISIONING_TRIGGERED",
        user_id=current_user["user_id"],
        resource_type="loan_application",
        resource_id=app_id,
        after={"active_analyzers": app.active_analyzers},
    )
    return {"pipeline_status": PipelineStatus.DECISIONING_IN_PROGRESS}


@router.post("/applications/{app_id}/bank-decision")
async def submit_bank_decision(
    app_id: str,
    payload: BankDecisionRequest,
    current_user: dict = Depends(_approver),
    db: AsyncSession = Depends(get_db),
):
    service = LoanApplicationService(db)
    app = await service.get_by_id(app_id)

    if app.pipeline_status != PipelineStatus.AWAITING_BANK_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit decision from status: {app.pipeline_status}",
        )

    app = await service.save_bank_decision(app_id, payload, current_user["user_id"])

    try:
        await OrchestratorClient().notify_bank_decision(
            external_application_id=app.external_application_id,
            final_decision=app.bank_final_decision,
            approved_amount=float(app.bank_approved_amount) if app.bank_approved_amount else None,
            interest_rate=float(app.bank_interest_rate) if app.bank_interest_rate else None,
            tenure_months=app.bank_tenure_months,
            monthly_emi=emi_from_application(
                app.bank_approved_amount, app.bank_interest_rate, app.bank_tenure_months
            ),
            counter_offer_options=app.llm_counter_offer_options,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Orchestrator notify failed: {e}")

    await AuditService(db).log(
        "BANK_DECISION_SUBMITTED",
        user_id=current_user["user_id"],
        resource_type="loan_application",
        resource_id=app_id,
        after={
            "final_decision": payload.final_decision,
            "approved_amount": payload.approved_amount,
            "interest_rate": payload.interest_rate,
            "override_reason": payload.override_reason,
        },
    )
    return {"pipeline_status": app.pipeline_status}
