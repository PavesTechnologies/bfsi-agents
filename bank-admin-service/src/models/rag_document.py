import uuid
import datetime
from typing import Optional
from sqlalchemy import String, Integer, BigInteger, DateTime, Text, ForeignKey, text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base


class RagDocument(Base):
    __tablename__ = "rag_documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    collection_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), server_default="PENDING", nullable=False, index=True)
    qdrant_point_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    chunk_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ingestion_log: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("bank_users.id", ondelete="SET NULL"), nullable=True)
    replaced_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))


class RagIngestionJob(Base):
    __tablename__ = "rag_ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("rag_documents.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), server_default="QUEUED", nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
