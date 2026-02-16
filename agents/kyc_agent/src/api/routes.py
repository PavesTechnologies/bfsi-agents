# src/api/routes.py

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID

from src.services.orchestrator import run_kyc

router = APIRouter()


class KYCRequest(BaseModel):
    application_id: UUID
    applicant_data: Dict[str, Any]
    documents: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/")
def greet():
    return {"message": "KYC Agent running"}


@router.post("/kyc/execute")
async def execute_kyc(request: Request, body: KYCRequest):
    return await run_kyc(request, body)
