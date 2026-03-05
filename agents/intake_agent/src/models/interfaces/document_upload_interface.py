# src/models/interfaces/document_interfaces.py
from pydantic import BaseModel
from uuid import UUID

class DocumentCreateRequest(BaseModel):
    application_id: UUID
    document_type: str

class DocumentCreateResponse(BaseModel):
    document_id: UUID
