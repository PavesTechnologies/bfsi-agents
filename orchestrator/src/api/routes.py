"""
API Routes for Orchestrator
"""

import asyncio
import json
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any, Deque, Dict, Optional

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
        await service.execute_full_pipeline(
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


class HumanReviewApproveRequest(BaseModel):
    application_id: str
    override_amount: Optional[float] = None
    override_rate: Optional[float] = None
    override_tenure: Optional[int] = None
    selected_offer_id: Optional[str] = None


class HumanReviewRejectRequest(BaseModel):
    application_id: str
    notes: Optional[str] = None


@router.post("/human_review/approve")
async def human_review_approve(request: HumanReviewApproveRequest):
    """Called by admin_service when a bank officer approves an application."""
    service = PipelineService()
    try:
        return await service.resume_after_human_review_approval(
            application_id=request.application_id,
            override_amount=request.override_amount,
            override_rate=request.override_rate,
            override_tenure=request.override_tenure,
            selected_offer_id=request.selected_offer_id,
            progress_callback=lambda event: _publish_event(request.application_id, event),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.post("/human_review/reject")
async def human_review_reject(request: HumanReviewRejectRequest):
    """Called by admin_service when a bank officer rejects an application."""
    service = PipelineService()
    try:
        return await service.resume_after_human_review_rejection(
            application_id=request.application_id,
            notes=request.notes,
            progress_callback=lambda event: _publish_event(request.application_id, event),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
