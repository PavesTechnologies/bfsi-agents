"""
API Routes for Orchestrator
"""

import asyncio
import json
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any, Deque, Dict, List, Optional as Opt

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.models.pipeline import (
    ApplicationTriggerRequest,
    ConfirmApprovalRequest,
    ResumeWithOfferRequest,
)
from src.services.pipeline_service import PipelineService

router = APIRouter()

HEARTBEAT_SECONDS = 15
EVENT_BUFFER_SIZE = 100
EVENT_TTL_SECONDS = 1800


class ProgressBroker:
    def __init__(
        self,
        max_events_per_application: int = EVENT_BUFFER_SIZE,
        ttl_seconds: int = EVENT_TTL_SECONDS,
    ):
        self._max_events = max_events_per_application
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = asyncio.Lock()
        self._buffers: Dict[str, Deque[Dict[str, Any]]] = {}
        self._subscribers: Dict[str, set[asyncio.Queue]] = {}
        self._terminal_at: Dict[str, datetime] = {}

    def _cleanup_expired_locked(self, now: datetime) -> None:
        expired_application_ids: list[str] = []
        for application_id, terminal_time in self._terminal_at.items():
            if (now - terminal_time) < self._ttl:
                continue
            if self._subscribers.get(application_id):
                continue
            expired_application_ids.append(application_id)

        for application_id in expired_application_ids:
            self._buffers.pop(application_id, None)
            self._terminal_at.pop(application_id, None)

    async def publish(self, application_id: str, event: Dict[str, Any]) -> None:
        async with self._lock:
            now = datetime.now(timezone.utc)
            self._cleanup_expired_locked(now)

            buffer = self._buffers.setdefault(
                application_id,
                deque(maxlen=self._max_events),
            )
            buffer.append(event)

            if event.get("is_terminal"):
                self._terminal_at[application_id] = now
            else:
                self._terminal_at.pop(application_id, None)

            queues = list(self._subscribers.get(application_id, set()))

        for queue in queues:
            queue.put_nowait(event)

    async def subscribe(
        self, application_id: str
    ) -> tuple[asyncio.Queue, list[Dict[str, Any]]]:
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._cleanup_expired_locked(datetime.now(timezone.utc))
            self._subscribers.setdefault(application_id, set()).add(queue)
            history = list(self._buffers.get(application_id, []))
        return queue, history

    async def unsubscribe(self, application_id: str, queue: asyncio.Queue) -> None:
        async with self._lock:
            queues = self._subscribers.get(application_id)
            if queues:
                queues.discard(queue)
                if not queues:
                    self._subscribers.pop(application_id, None)
            self._cleanup_expired_locked(datetime.now(timezone.utc))


progress_broker = ProgressBroker(ttl_seconds=EVENT_TTL_SECONDS)
active_pipeline_tasks: Dict[str, asyncio.Task] = {}


def _enrich_event(event: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(event)
    enriched.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    return enriched


async def _publish_event(application_id: str, event: Dict[str, Any]) -> None:
    await progress_broker.publish(application_id, _enrich_event(event))


async def _run_pipeline(application_id: str, raw_application: Dict[str, Any]) -> None:
    service = PipelineService()
    try:
        await service.execute_until_bank_review(
            application_id=application_id,
            raw_application=raw_application,
            progress_callback=lambda event: _publish_event(application_id, event),
        )
    except Exception as exc:
        await _publish_event(
            application_id,
            {
                "application_id": application_id,
                "event": "PIPELINE_FAILED",
                "stage": "ORCHESTRATOR",
                "status": "failed",
                "message": "Pipeline execution failed",
                "details": {"reason": str(exc)},
                "is_terminal": True,
            },
        )
    finally:
        await service.close()
        active_pipeline_tasks.pop(application_id, None)


async def _run_decisioning_task(application_id: str, active_analyzers: list | None) -> None:
    service = PipelineService()
    try:
        await service.run_decisioning(
            application_id=application_id,
            active_analyzers=active_analyzers,
            progress_callback=lambda event: _publish_event(application_id, event),
        )
    except Exception as exc:
        await _publish_event(
            application_id,
            {
                "application_id": application_id,
                "event": "PIPELINE_FAILED",
                "stage": "DECISIONING",
                "status": "failed",
                "message": "Decisioning task failed",
                "details": {"reason": str(exc)},
                "is_terminal": True,
            },
        )
    finally:
        await service.close()


class ApplicationTriggerAcceptedResponse(BaseModel):
    application_id: str
    accepted: bool
    stream_url: str


@router.get("/")
def health_check():
    return {"status": "ok", "service": "orchestrator"}


@router.post("/trigger_pipeline")
async def trigger_pipeline(request: ApplicationTriggerRequest):
    """
    Triggers the pipeline until a user decision is required or it is declined.
    """
    service = PipelineService()
    try:
        return await service.execute_until_decision(
            application_id=request.application_id,
            raw_application=request.raw_application,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.post("/trigger_pipeline_async", response_model=ApplicationTriggerAcceptedResponse)
async def trigger_pipeline_async(request: ApplicationTriggerRequest):
    """
    Accepts a pipeline run and returns immediately.
    Use /pipeline_updates/{application_id} to consume progress events.
    """
    existing_task = active_pipeline_tasks.get(request.application_id)
    if existing_task and not existing_task.done():
        return ApplicationTriggerAcceptedResponse(
            application_id=request.application_id,
            accepted=True,
            stream_url=f"/pipeline_updates/{request.application_id}",
        )

    await _publish_event(
        request.application_id,
        {
            "application_id": request.application_id,
            "event": "PIPELINE_ACCEPTED",
            "stage": "ORCHESTRATOR",
            "status": "started",
            "message": "Pipeline accepted for processing",
            "is_terminal": False,
        },
    )

    task = asyncio.create_task(
        _run_pipeline(
            application_id=request.application_id,
            raw_application=request.raw_application,
        )
    )
    active_pipeline_tasks[request.application_id] = task

    return ApplicationTriggerAcceptedResponse(
        application_id=request.application_id,
        accepted=True,
        stream_url=f"/pipeline_updates/{request.application_id}",
    )


@router.get("/pipeline_updates/{application_id}")
async def pipeline_updates(application_id: str):
    """
    Streams pipeline progress events as Server-Sent Events (SSE).
    """
    queue, history = await progress_broker.subscribe(application_id)

    async def event_generator():
        try:
            for event in history:
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("is_terminal"):
                    return

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("is_terminal"):
                        return
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            await progress_broker.unsubscribe(application_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/select_counter_offer")
async def select_counter_offer(request: ResumeWithOfferRequest):
    """Resume disbursement after the user chooses a counter offer."""
    service = PipelineService()
    try:
        return await service.resume_after_counter_offer_selection(
            application_id=request.application_id,
            selected_offer_id=request.selected_offer_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.post("/confirm_approval")
async def confirm_approval(request: ConfirmApprovalRequest):
    """Resume or cancel an approved application based on user confirmation."""
    service = PipelineService()
    try:
        if not request.accepted:
            return service.cancel_pending_application(request.application_id)
        return await service.resume_after_approval_confirmation(
            application_id=request.application_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


# ── HITL Internal Callbacks (called by bank-admin-service) ───────────────────

class RunDecisioningRequest(BaseModel):
    active_analyzers: Opt[List[str]] = None


class NotifyBankDecisionRequest(BaseModel):
    final_decision: str
    approved_amount: Opt[float] = None
    interest_rate: Opt[float] = None
    tenure_months: Opt[int] = None
    monthly_emi: Opt[float] = None
    counter_offer_options: Opt[List[Any]] = None


@router.post("/internal/run-decisioning/{application_id}", status_code=202)
async def internal_run_decisioning(
    application_id: str,
    request: RunDecisioningRequest,
):
    """Called by bank-admin-service when bank employee triggers decisioning."""
    asyncio.create_task(
        _run_decisioning_task(application_id, request.active_analyzers)
    )
    return {"status": "decisioning_started", "application_id": application_id}


@router.post("/internal/notify-bank-decision/{application_id}")
async def internal_notify_bank_decision(
    application_id: str,
    request: NotifyBankDecisionRequest,
):
    """Called by bank-admin-service after bank employee submits their decision."""
    service = PipelineService()
    try:
        await service.notify_applicant_of_bank_decision(
            application_id=application_id,
            final_decision=request.final_decision,
            approved_amount=request.approved_amount,
            interest_rate=request.interest_rate,
            tenure_months=request.tenure_months,
            monthly_emi=request.monthly_emi,
            counter_offer_options=request.counter_offer_options,
            progress_callback=lambda event: _publish_event(application_id, event),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
    return {"status": "notified", "application_id": application_id}


# ── Applicant Action Endpoints ────────────────────────────────────────────────

@router.post("/pipeline/{application_id}/accept")
async def pipeline_accept(application_id: str):
    """Applicant accepts the bank offer — moves to signature stage."""
    service = PipelineService()
    try:
        await service.applicant_accept(
            application_id=application_id,
            progress_callback=lambda event: _publish_event(application_id, event),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
    return {"status": "AWAITING_SIGNATURE", "application_id": application_id}


@router.post("/pipeline/{application_id}/decline")
async def pipeline_decline(application_id: str):
    """Applicant declines the bank offer — terminates the pipeline."""
    service = PipelineService()
    try:
        await service.applicant_decline(
            application_id=application_id,
            progress_callback=lambda event: _publish_event(application_id, event),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
    return {"status": "DECLINED_BY_APPLICANT", "application_id": application_id}


class SignatureRequest(BaseModel):
    full_name: str
    agreed: bool
    ip: Opt[str] = None
    user_agent: Opt[str] = None


@router.post("/pipeline/{application_id}/signature")
async def pipeline_signature(application_id: str, request: SignatureRequest):
    """Applicant submits digital signature — triggers disbursement."""
    service = PipelineService()
    try:
        result = await service.submit_signature(
            application_id=application_id,
            full_name=request.full_name,
            agreed=request.agreed,
            ip=request.ip,
            user_agent=request.user_agent,
            progress_callback=lambda event: _publish_event(application_id, event),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
    return {"status": "DISBURSED", "application_id": application_id, "disbursement_receipt": result}


@router.get("/pipeline/{application_id}/status")
async def pipeline_status(application_id: str):
    """Return the current in-memory pipeline state for an application."""
    from src.store.pipeline_state_store import get_state
    state = get_state(application_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"No state for application {application_id}")
    return {
        "application_id": application_id,
        "phase": state.get("phase"),
        "bank_decision": state.get("bank_decision"),
        "approved_amount": state.get("approved_amount"),
        "interest_rate": state.get("interest_rate"),
        "tenure_months": state.get("tenure_months"),
        "monthly_emi": state.get("monthly_emi"),
        "counter_offer_options": state.get("counter_offer_options"),
    }
