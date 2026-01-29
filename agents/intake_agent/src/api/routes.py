from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from src.services.orchestrator import run_agent
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from src.core.database import get_db

from src.core.database import get_db
from src.repositories.idempotency_repository import IdempotencyRepository
from src.utils.hash import stable_payload_hash
from src.models.schemas import IntakeRequest
router = APIRouter()


class DecisionRequest(BaseModel):
    input_text: str


@router.get("/")
def greet():
    return "Hello world!"

@router.post("/decide")
def decide(request: DecisionRequest):
    return run_agent(request.input_text)
@router.post("/v1/intake", status_code=202)
async def intake(
    request: IntakeRequest,
    db=Depends(get_db)
):
    repo = IdempotencyRepository(db)

    payload_hash = stable_payload_hash(request.payload)

    existing = await repo.get(request.request_id)

    if existing:
        if existing.request_hash != payload_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payload mismatch for same request_id"
            )

        if existing.status == "COMPLETED":
            return existing.response_payload

        return {
            "request_id": str(request.request_id),
            "status": "accepted"
        }

    try:
        await repo.create(
            request_id=request.request_id,
            app_id=request.app_id,
            request_hash=payload_hash
        )
    except IntegrityError:
        # Race condition fallback
        return {
            "request_id": str(request.request_id),
            "status": "accepted"
        }

    # 🔹 enqueue async job here (next section)

    return {
        "request_id": str(request.request_id),
        "status": "accepted"
    }