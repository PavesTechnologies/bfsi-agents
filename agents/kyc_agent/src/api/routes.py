# src/api/routes.py

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.services.orchestrator import run_kyc

router = APIRouter()


class KYCRequest(BaseModel):
    application_id: UUID
    applicant_data: dict[str, Any]
    documents: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@router.get("/")
def greet():
    return {"message": "KYC Agent running"}


@router.post("/kyc/execute")
async def execute_kyc(request: Request, body: KYCRequest):
    return await run_kyc(request, body)
