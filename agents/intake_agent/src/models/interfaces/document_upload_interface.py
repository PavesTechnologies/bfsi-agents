# src/models/interfaces/document_interfaces.py
from uuid import UUID

from pydantic import BaseModel


class DocumentCreateRequest(BaseModel):
    application_id: UUID
    document_type: str


class DocumentCreateResponse(BaseModel):
    document_id: UUID
