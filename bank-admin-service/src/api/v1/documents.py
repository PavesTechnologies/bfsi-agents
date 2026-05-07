from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, require_permission
from src.core.permissions import Permission
from src.schemas.document import DocumentOut, DocumentListResponse, IngestionJobOut
from src.services.rag_ingestion_service import RagIngestionService
from src.services.rag_file_service import RagFileService
from src.services.audit_service import AuditService
from src.workers.rag_worker import run_ingestion

router = APIRouter(prefix="/documents", tags=["Documents"])

_viewer = require_permission(Permission.VIEW_DOCUMENTS)
_uploader = require_permission(Permission.UPLOAD_DOCUMENTS)
_replacer = require_permission(Permission.REPLACE_DOCUMENTS)
_deleter = require_permission(Permission.DELETE_DOCUMENTS)


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    collection: Optional[str] = Query(None, description="rbi_guidelines | bank_policies"),
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    service = RagIngestionService(db)
    items = await service.list_documents(collection)
    return DocumentListResponse(items=items, total=len(items))


@router.post("/", response_model=IngestionJobOut, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    document_name: str = Form(...),
    current_user: dict = Depends(_uploader),
    db: AsyncSession = Depends(get_db),
):
    service = RagIngestionService(db)
    doc, job = await service.upload_document(file, collection_name, document_name, current_user["user_id"])
    await AuditService(db).log("DOCUMENT_UPLOADED", user_id=current_user["user_id"], resource_type="rag_document", resource_id=str(doc.id), after={"document_name": document_name, "collection": collection_name})
    background_tasks.add_task(run_ingestion, str(doc.id))
    return job


@router.post("/{document_id}/replace", response_model=IngestionJobOut, status_code=202)
async def replace_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_name: str = Form(...),
    current_user: dict = Depends(_replacer),
    db: AsyncSession = Depends(get_db),
):
    service = RagIngestionService(db)
    old_doc = await service.get_document(document_id)
    doc, job = await service.upload_document(file, old_doc.collection_name, document_name, current_user["user_id"], replace_id=document_id)
    await AuditService(db).log("DOCUMENT_REPLACED", user_id=current_user["user_id"], resource_type="rag_document", resource_id=document_id, after={"new_document_id": str(doc.id), "document_name": document_name})
    background_tasks.add_task(run_ingestion, str(doc.id))
    return job


@router.get("/ingestion-jobs", response_model=list[IngestionJobOut])
async def list_ingestion_jobs(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await RagIngestionService(db).list_jobs(limit)


@router.get("/ingestion-jobs/{job_id}", response_model=IngestionJobOut)
async def get_ingestion_job(
    job_id: str,
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await RagIngestionService(db).get_ingestion_job(job_id)


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: str,
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await RagIngestionService(db).get_document(document_id)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(_deleter),
    db: AsyncSession = Depends(get_db),
):
    await RagIngestionService(db).delete_document(document_id)
    await AuditService(db).log("DOCUMENT_DELETED", user_id=current_user["user_id"], resource_type="rag_document", resource_id=document_id)


# ── Physical source files (disk) ─────────────────────────────────────────────

@router.get("/source-files", response_model=list[dict])
async def list_source_files(current_user: dict = Depends(_viewer)):
    return RagFileService().list_files()


@router.post("/source-files", status_code=201)
async def upload_source_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(_uploader),
    db: AsyncSession = Depends(get_db),
):
    info = await RagFileService().save_file(file)
    await AuditService(db).log(
        "SOURCE_FILE_UPLOADED",
        user_id=current_user["user_id"],
        resource_type="source_file",
        resource_id=info["filename"],
        after=info,
    )
    return info


@router.delete("/source-files/{filename}", status_code=204)
async def delete_source_file(
    filename: str,
    current_user: dict = Depends(_deleter),
    db: AsyncSession = Depends(get_db),
):
    RagFileService().delete_file(filename)
    await AuditService(db).log(
        "SOURCE_FILE_DELETED",
        user_id=current_user["user_id"],
        resource_type="source_file",
        resource_id=filename,
    )


@router.post("/source-files/trigger-ingestion")
async def trigger_ingestion(
    current_user: dict = Depends(_uploader),
    db: AsyncSession = Depends(get_db),
):
    result = await RagFileService().trigger_reingestion()
    await AuditService(db).log(
        "RAG_REINGESTION_TRIGGERED",
        user_id=current_user["user_id"],
        resource_type="rag_ingestion",
        resource_id="refresh",
    )
    return result
