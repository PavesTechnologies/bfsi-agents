from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.intake_database.db_session import get_db
from src.services.intake_services.document_upload_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


# -------------------------------
# Internal helper (DO NOT expose)
# -------------------------------
async def _upload_with_document_type(
    *,
    db: AsyncSession,
    application_id: str,
    file: UploadFile,
    document_type: str,
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
        "document_type": document.document_type,
    }


# -------------------------------
# SSN Card
# -------------------------------
@router.post("/upload/ssn-card")
async def upload_ssn_card(
    application_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    return await _upload_with_document_type(
        db=db,
        application_id=application_id,
        file=file,
        document_type="ssn_card",
    )


# -------------------------------
# Passport
# -------------------------------
@router.post("/upload/passport")
async def upload_passport(
    application_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    return await _upload_with_document_type(
        db=db,
        application_id=application_id,
        file=file,
        document_type="passport",
    )


# -------------------------------
# Driver's License
# -------------------------------
@router.post("/upload/drivers-license")
async def upload_drivers_license(
    application_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    return await _upload_with_document_type(
        db=db,
        application_id=application_id,
        file=file,
        document_type="drivers_license",
    )


# -------------------------------
# State ID
# -------------------------------
@router.post("/upload/state-id")
async def upload_state_id(
    application_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    return await _upload_with_document_type(
        db=db,
        application_id=application_id,
        file=file,
        document_type="state_id",
    )


# -------------------------------
# W2
# -------------------------------
@router.post("/upload/w2")
async def upload_w2(
    application_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    return await _upload_with_document_type(
        db=db,
        application_id=application_id,
        file=file,
        document_type="w2",
    )


# -------------------------------
# Pay Stub
# -------------------------------
@router.post("/upload/pay-stub")
async def upload_pay_stub(
    application_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    return await _upload_with_document_type(
        db=db,
        application_id=application_id,
        file=file,
        document_type="pay_stub",
    )


# -------------------------------
# Bank Statement
# -------------------------------
@router.post("/upload/bank-statement")
async def upload_bank_statement(
    application_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    return await _upload_with_document_type(
        db=db,
        application_id=application_id,
        file=file,
        document_type="bank_statement",
    )


# -------------------------------
# Photo
# -------------------------------
@router.post("/upload/photo")
async def upload_photo(
    application_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    return await _upload_with_document_type(
        db=db,
        application_id=application_id,
        file=file,
        document_type="photo",
    )
