import io
import mimetypes
import zipfile
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.document_classification.document_ocr_classifier import (
    classify_document_from_bytes,
)
from src.domain.document_classification.document_type import DocumentType
from src.services.intake_services.document_upload_service import DocumentService
from src.repositories.intake_repo.loan_info_repo import LoanInfoDAO

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"}
MAX_FILES_PER_ZIP = 20
MAX_ZIP_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

_MIME_FALLBACKS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tiff": "image/tiff",
    ".bmp": "image/bmp",
    ".pdf": "application/pdf",
}


class ZipProcessor:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.document_service = DocumentService(db)
        self.loan_info_dao = LoanInfoDAO(db)

    async def process_zip(self, application_id: str, zip_bytes: bytes) -> dict:
        try:
            application_id_obj = UUID(application_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid application_id format.")

        application = await self.loan_info_dao.get_loan_application_by_id(application_id_obj)
        if not application:
            raise HTTPException(
                status_code=404,
                detail=f"No loan application found with id {application_id}",
            )

        if len(zip_bytes) > MAX_ZIP_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="ZIP file exceeds 50 MB limit",
            )

        try:
            zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid ZIP archive")

        entries = [
            e for e in zf.namelist()
            if not e.startswith("__MACOSX") and not e.endswith("/")
        ]

        if len(entries) > MAX_FILES_PER_ZIP:
            raise HTTPException(
                status_code=400,
                detail=f"ZIP contains {len(entries)} files; maximum allowed is {MAX_FILES_PER_ZIP}",
            )

        results = []
        for entry in entries:
            ext = Path(entry).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                results.append({
                    "file": entry,
                    "status": "SKIPPED",
                    "reason": f"Unsupported extension: {ext}",
                })
                continue

            file_bytes = zf.read(entry)
            mime = (
                mimetypes.guess_type(entry)[0]
                or _MIME_FALLBACKS.get(ext, "application/octet-stream")
            )

            # --- OCR-based classification ---
            try:
                classification = classify_document_from_bytes(file_bytes, mime)
            except Exception as exc:
                results.append({
                    "file": entry,
                    "status": "SKIPPED",
                    "reason": f"OCR failed: {exc}",
                })
                continue

            if classification.doc_type == DocumentType.UNKNOWN:
                results.append({
                    "file": entry,
                    "status": "SKIPPED",
                    "reason": (
                        f"Could not classify document (confidence={classification.confidence}). "
                        "Ensure the document is one of: aadhaar, pan, voter_id, form_16, "
                        "salary_slip, itr, passport."
                    ),
                    "ocr_confidence": classification.confidence,
                })
                continue

            doc_type = str(classification.doc_type)
            upload_file = _BytesUploadFile(filename=entry, content=file_bytes, content_type=mime)

            try:
                await self.document_service.upload_document(
                    application_id=application_id,
                    document_type=doc_type,
                    file=upload_file,
                    pre_classification=classification,  # reuse — avoids a second OCR call
                )
                results.append({
                    "file": entry,
                    "status": "PROCESSED",
                    "doc_type": doc_type,
                    "ocr_confidence": classification.confidence,
                })
            except HTTPException as exc:
                results.append({
                    "file": entry,
                    "status": "FAILED",
                    "doc_type": doc_type,
                    "ocr_confidence": classification.confidence,
                    "reason": exc.detail,
                })

        zf.close()

        processed = sum(1 for r in results if r["status"] == "PROCESSED")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        skipped = sum(1 for r in results if r["status"] == "SKIPPED")

        return {
            "application_id": application_id,
            "total_files": len(entries),
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "documents": results,
        }


class _BytesUploadFile:
    """Minimal shim so ZipProcessor can pass raw bytes into DocumentService."""

    def __init__(self, filename: str, content: bytes, content_type: str):
        self.filename = filename
        self.content_type = content_type
        self.size = len(content)
        self._content = content

    async def read(self) -> bytes:
        return self._content
