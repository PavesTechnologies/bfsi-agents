from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.intake_database.db_session import get_db
from src.services.intake_services.document_upload_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

@router.post("/upload")
async def upload_document(
    application_id: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)

    document = await service.upload_document(
        application_id=application_id,
        document_type=document_type,
        file=file,
    )

    return {
        "message": "Document uploaded successfully",
        "document_id": str(document.id),
        "file_name": document.file_name,
        "mime_type": document.mime_type,
        "file_size": document.file_size,
    }
