import uuid
import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    collection_name: str
    document_name: str
    original_filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    status: str
    chunk_count: Optional[int] = None
    uploaded_by: Optional[uuid.UUID] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentOut]
    total: int


class IngestionJobOut(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    progress_pct: int
    error_message: Optional[str] = None
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
