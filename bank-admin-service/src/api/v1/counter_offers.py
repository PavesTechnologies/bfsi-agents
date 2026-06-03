"""
Counter Offer API — bank-admin-service

Bank-employee endpoints for reviewing, editing, and publishing LLM-generated
counter offers. One internal endpoint (no JWT) receives the decisioning agent's
COUNTER_OFFER result from the orchestrator.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, require_permission
from src.core.permissions import Permission
from pydantic import BaseModel

from src.schemas.counter_offer import (
    CounterOfferSessionCreateInternal,
    CounterOfferSessionResponse,
    EditLogEntryResponse,
    ManualOfferCreateRequest,
    OfferOptionCreateRequest,
    OfferOptionUpdateRequest,
    RecommendRequest,
)
from src.services.audit_service import AuditService
from src.services.counter_offer_service import CounterOfferService

router = APIRouter(prefix="/counter-offers", tags=["Counter Offers"])

_viewer = require_permission(Permission.VIEW_APPLICATIONS)
_reviewer = require_permission(Permission.REVIEW_COUNTER_OFFERS)


# ── Orchestrator callback (no JWT — internal network only) ───────────────────

@router.post("/internal", status_code=201, include_in_schema=False)
async def create_counter_offer_session(
    payload: CounterOfferSessionCreateInternal,
    db: AsyncSession = Depends(get_db),
):
    """Called by the orchestrator when the decisioning agent returns COUNTER_OFFER.

    Creates a counter_offer_session row and advances the application status to
    COUNTER_OFFER_REVIEW so bank employees can see it in their review queue.
    """
    session = await CounterOfferService(db).create_session(payload)
    return {"session_id": str(session.id), "status": session.status}


class _ApplicantAcceptBody(BaseModel):
    option_id: str


# ── Orchestrator callbacks (no JWT) — applicant response recording ────────────

@router.post(
    "/internal/by-external/{external_id}/applicant-accept",
    status_code=200,
    include_in_schema=False,
)
async def record_applicant_accept(
    external_id: str,
    body: _ApplicantAcceptBody,
    db: AsyncSession = Depends(get_db),
):
    """Called by the orchestrator when the applicant selects a counter-offer option.

    Marks the session APPLICANT_RESPONDED with the chosen option and advances
    the application status to AWAITING_SIGNATURE.
    """
    session = await CounterOfferService(db).record_applicant_accept(external_id, body.option_id)
    return {"session_id": str(session.id), "accepted_option_id": session.accepted_option_id}


@router.post(
    "/internal/by-external/{external_id}/applicant-decline",
    status_code=200,
    include_in_schema=False,
)
async def record_applicant_decline(
    external_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Called by the orchestrator when the applicant declines all counter offers.

    Marks the session APPLICANT_RESPONDED and cancels the application.
    """
    session = await CounterOfferService(db).record_applicant_decline(external_id)
    return {"session_id": str(session.id), "applicant_decision": session.applicant_decision}


# ── Bank-employee read endpoints ─────────────────────────────────────────────

@router.get("/applications/{application_id}", response_model=CounterOfferSessionResponse)
async def get_counter_offer_session(
    application_id: uuid.UUID,
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    """Fetch the most recent counter offer session for an application."""
    session = await CounterOfferService(db).get_by_application_id(application_id)
    return CounterOfferSessionResponse.model_validate(session)


@router.get("/{session_id}/edit-log", response_model=list[EditLogEntryResponse])
async def get_edit_log(
    session_id: uuid.UUID,
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    """Full chronological audit trail for a counter offer session."""
    logs = await CounterOfferService(db).get_edit_log(session_id)
    return [EditLogEntryResponse.model_validate(entry) for entry in logs]


# ── Bank-initiated manual offer on a declined application ─────────────────────

@router.post("/applications/{application_id}/manual-offer", status_code=201)
async def create_manual_offer(
    application_id: uuid.UUID,
    payload: ManualOfferCreateRequest,
    current_user: dict = Depends(_reviewer),
    db: AsyncSession = Depends(get_db),
):
    """Create a bank-initiated counter offer for a DECLINED application.

    Seeds a DRAFT session with one editable option, moves the application into
    COUNTER_OFFER_REVIEW, and re-opens the orchestrator pipeline. The bank then
    edits/adds options and publishes via the standard endpoints. Returns the new
    session id so the UI can navigate to the Counter-Offer Review page.
    """
    service = CounterOfferService(db)
    session = await service.create_manual_session(
        str(application_id), current_user["user_id"], payload
    )
    await AuditService(db).log(
        "COUNTER_OFFER_MANUAL_CREATED",
        user_id=current_user["user_id"],
        resource_type="counter_offer_session",
        resource_id=str(session.id),
        after={"application_id": str(application_id), "status": session.status},
    )
    return {"session_id": str(session.id), "status": session.status}


# ── Bank-employee edit endpoints (REVIEW_COUNTER_OFFERS required) ─────────────

@router.patch("/{session_id}/options/{option_id}", response_model=CounterOfferSessionResponse)
async def update_offer_option(
    session_id: uuid.UUID,
    option_id: str,
    payload: OfferOptionUpdateRequest,
    current_user: dict = Depends(_reviewer),
    db: AsyncSession = Depends(get_db),
):
    """Edit one or more fields of an existing offer option.

    If any financial field (amount / tenure / rate) changes, the server
    automatically recalculates EMI, disbursement, total repayment, and
    affordability headroom. The LLM-generated `generated_options` snapshot
    is never modified; only `current_options` is updated.
    """
    service = CounterOfferService(db)
    session = await service.update_option(session_id, option_id, payload, current_user["user_id"])
    await AuditService(db).log(
        "COUNTER_OFFER_OPTION_EDITED",
        user_id=current_user["user_id"],
        resource_type="counter_offer_session",
        resource_id=str(session_id),
        after={"option_id": option_id, **payload.model_dump(exclude_none=True, exclude={"note"})},
    )
    return CounterOfferSessionResponse.model_validate(session)


@router.post("/{session_id}/options", response_model=CounterOfferSessionResponse, status_code=201)
async def add_offer_option(
    session_id: uuid.UUID,
    payload: OfferOptionCreateRequest,
    current_user: dict = Depends(_reviewer),
    db: AsyncSession = Depends(get_db),
):
    """Add a bank-created custom offer option. Derived fields are computed server-side."""
    service = CounterOfferService(db)
    session = await service.add_option(session_id, payload, current_user["user_id"])
    await AuditService(db).log(
        "COUNTER_OFFER_OPTION_ADDED",
        user_id=current_user["user_id"],
        resource_type="counter_offer_session",
        resource_id=str(session_id),
        after=payload.model_dump(),
    )
    return CounterOfferSessionResponse.model_validate(session)


@router.delete("/{session_id}/options/{option_id}", response_model=CounterOfferSessionResponse)
async def delete_offer_option(
    session_id: uuid.UUID,
    option_id: str,
    current_user: dict = Depends(_reviewer),
    db: AsyncSession = Depends(get_db),
):
    """Delete a bank-added custom option. CO1, CO2, CO3 cannot be deleted."""
    service = CounterOfferService(db)
    session = await service.delete_option(session_id, option_id, current_user["user_id"])
    await AuditService(db).log(
        "COUNTER_OFFER_OPTION_DELETED",
        user_id=current_user["user_id"],
        resource_type="counter_offer_session",
        resource_id=str(session_id),
        after={"option_id": option_id},
    )
    return CounterOfferSessionResponse.model_validate(session)


@router.patch("/{session_id}/recommend", response_model=CounterOfferSessionResponse)
async def set_recommended_option(
    session_id: uuid.UUID,
    payload: RecommendRequest,
    current_user: dict = Depends(_reviewer),
    db: AsyncSession = Depends(get_db),
):
    """Change which offer option is marked as recommended.

    The change is recorded in the edit log. is_recommended is kept in sync
    across all options in current_options automatically.
    """
    service = CounterOfferService(db)
    session = await service.set_recommended(session_id, payload, current_user["user_id"])
    await AuditService(db).log(
        "COUNTER_OFFER_RECOMMENDATION_CHANGED",
        user_id=current_user["user_id"],
        resource_type="counter_offer_session",
        resource_id=str(session_id),
        after={"recommended_option_id": payload.option_id},
    )
    return CounterOfferSessionResponse.model_validate(session)


@router.post("/{session_id}/publish", response_model=CounterOfferSessionResponse)
async def publish_counter_offers(
    session_id: uuid.UUID,
    current_user: dict = Depends(_reviewer),
    db: AsyncSession = Depends(get_db),
):
    """Publish the current offer set to the applicant.

    Transitions session status DRAFT → PUBLISHED and application status
    COUNTER_OFFER_REVIEW → AWAITING_APPLICANT_RESPONSE. Rejected if already
    expired.
    """
    service = CounterOfferService(db)
    session = await service.publish(session_id, current_user["user_id"])
    await AuditService(db).log(
        "COUNTER_OFFERS_PUBLISHED",
        user_id=current_user["user_id"],
        resource_type="counter_offer_session",
        resource_id=str(session_id),
        after={
            "status": session.status,
            "recommended_option_id": session.recommended_option_id,
            "options_count": len(session.current_options),
        },
    )
    return CounterOfferSessionResponse.model_validate(session)
