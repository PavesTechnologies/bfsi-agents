import uuid
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.repositories.intake_repo.document_upload_repo import LoanIntakeDAO

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/jpg",
}

ALLOWED_DOCUMENT_TYPES = {
    "passport",
    "drivers_license",
    "state_id",
    "ssn_card",
    "visa",
    "i94",
    "bank_statement",
    "pay_stub",
    "photo",
}

class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = LoanIntakeDAO(db)

    async def upload_document(
        self,
        application_id: str,
        document_type: str,
        file: UploadFile,
    ):
        # ✅ document type validation
        if document_type not in ALLOWED_DOCUMENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document_type. Allowed values: {sorted(ALLOWED_DOCUMENT_TYPES)}",
            )

        # ✅ mime-type validation
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF or image files are allowed",
            )

        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )

        try:
            document = await self.dao.create_document({
                "id": uuid.uuid4(),
                "application_id": uuid.UUID(application_id),
                "document_type": document_type,
                "file_name": file.filename,
                "mime_type": file.content_type,
                "file_size": len(file_bytes),
                "content": file_bytes,
            })

            await self.db.commit()
            await self.db.refresh(document)

            return document

        except SQLAlchemyError:
            await self.db.rollback()
            raise
