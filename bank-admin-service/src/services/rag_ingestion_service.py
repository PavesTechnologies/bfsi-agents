"""
RAG ingestion service: parses uploaded PDFs, chunks them,
embeds with sentence-transformers, and upserts into Qdrant.
"""
import asyncio
import uuid
import logging
import os
import tempfile
import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile, HTTPException

from src.models.rag_document import RagDocument, RagIngestionJob
from src.schemas.document import DocumentOut, IngestionJobOut
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

VALID_COLLECTIONS = {"rbi_guidelines", "bank_policies"}


class RagIngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_document(
        self,
        file: UploadFile,
        collection_name: str,
        document_name: str,
        user_id: str,
        replace_id: Optional[str] = None,
    ) -> tuple[DocumentOut, IngestionJobOut]:
        if collection_name not in VALID_COLLECTIONS:
            raise HTTPException(status_code=400, detail=f"collection_name must be one of {VALID_COLLECTIONS}")
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")

        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

        # Serialize concurrent uploads to the same collection — only one ingestion at a time.
        in_flight = await self.db.execute(
            select(RagDocument).where(
                RagDocument.collection_name == collection_name,
                RagDocument.status.in_(("PENDING", "PROCESSING")),
            )
        )
        if in_flight.scalars().first() is not None:
            raise HTTPException(
                status_code=409,
                detail="An ingestion is already in progress for this collection. Wait for it to finish.",
            )

        # Auto-derive lineage: if caller didn't specify replace_id, point at the current ACTIVE row.
        resolved_replace_id: Optional[uuid.UUID]
        if replace_id:
            resolved_replace_id = uuid.UUID(replace_id)
        else:
            current_active = await self.db.execute(
                select(RagDocument).where(
                    RagDocument.collection_name == collection_name,
                    RagDocument.status == "ACTIVE",
                ).order_by(RagDocument.created_at.desc())
            )
            active_row = current_active.scalars().first()
            resolved_replace_id = active_row.id if active_row else None

        storage_path = await self._store_file(content, file.filename)

        doc = RagDocument(
            collection_name=collection_name,
            document_name=document_name,
            original_filename=file.filename,
            storage_path=storage_path,
            file_size_bytes=len(content),
            mime_type="application/pdf",
            status="PENDING",
            uploaded_by=uuid.UUID(user_id),
            replaced_document_id=resolved_replace_id,
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)

        job = RagIngestionJob(document_id=doc.id, status="QUEUED")
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)

        return DocumentOut.model_validate(doc), IngestionJobOut.model_validate(job)

    async def _store_file(self, content: bytes, filename: str) -> str:
        if settings.use_s3:
            return await self._store_s3(content, filename)
        return await self._store_local(content, filename)

    async def _store_local(self, content: bytes, filename: str) -> str:
        upload_dir = Path("/tmp/bfsi_rag_uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{uuid.uuid4()}_{filename}"
        path = upload_dir / unique_name
        path.write_bytes(content)
        return str(path)

    async def _store_s3(self, content: bytes, filename: str) -> str:
        import boto3
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        key = f"rag-uploads/{uuid.uuid4()}/{filename}"
        s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=content, ContentType="application/pdf")
        return f"s3://{settings.S3_BUCKET}/{key}"

    async def list_documents(self, collection_name: Optional[str] = None) -> list[DocumentOut]:
        query = select(RagDocument).order_by(RagDocument.created_at.desc())
        if collection_name:
            query = query.where(RagDocument.collection_name == collection_name)
        result = await self.db.execute(query)
        docs = result.scalars().all()
        return [DocumentOut.model_validate(d) for d in docs]

    async def get_document(self, document_id: str) -> DocumentOut:
        result = await self.db.execute(select(RagDocument).where(RagDocument.id == uuid.UUID(document_id)))
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentOut.model_validate(doc)

    async def get_ingestion_job(self, job_id: str) -> IngestionJobOut:
        result = await self.db.execute(select(RagIngestionJob).where(RagIngestionJob.id == uuid.UUID(job_id)))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return IngestionJobOut.model_validate(job)

    async def list_jobs(self, limit: int = 20) -> list[IngestionJobOut]:
        result = await self.db.execute(
            select(RagIngestionJob).order_by(RagIngestionJob.created_at.desc()).limit(limit)
        )
        return [IngestionJobOut.model_validate(j) for j in result.scalars().all()]

    async def delete_document(self, document_id: str) -> None:
        result = await self.db.execute(select(RagDocument).where(RagDocument.id == uuid.UUID(document_id)))
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        if doc.status == "PROCESSING":
            raise HTTPException(status_code=409, detail="Cannot delete a document currently being processed")

        was_active = doc.status == "ACTIVE"
        doc.status = "DELETED"
        doc.qdrant_point_ids = None
        await self.db.flush()

        if was_active:
            # Deleting the only active doc in a collection should leave Qdrant empty too.
            from src.workers.rag_worker import _get_qdrant_client, _wipe_collection
            try:
                client = _get_qdrant_client()
                await asyncio.to_thread(_wipe_collection, client, doc.collection_name)
            except Exception as exc:
                logger.warning(f"Failed to wipe Qdrant collection {doc.collection_name} on delete: {exc}")
