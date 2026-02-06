import os
import uuid
from io import BytesIO

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from PIL import Image

from src.repositories.intake_repo.document_upload_repo import LoanIntakeDAO
from src.domain.image_processing.preprocessor import preprocess

# Existing validations (KEEP)
from src.domain.document_validation.ssn_card_doc_validation import ssn_card_validation
from src.domain.document_validation.aws_passport_validation import PassportOCR

# OCR (AWS Textract ONLY)
from src.domain.ocr.ocr_dispatcher import extract_ocr

# Keyword-based intent validation (NEW)
from src.domain.document_validation.keyword_document_validator import (
    KeywordDocumentValidator,
)
from src.domain.document_classification.document_type import DocumentType


# -----------------------------
# Document rules (centralized)
# -----------------------------

DOCUMENT_RULES = {
    "passport": {
        "mime_types": {"application/pdf", "image/jpeg", "image/png"},
        "max_size_mb": 5,
        "max_resolution": (5000, 5000),
    },
    "drivers_license": {
        "mime_types": {"image/jpeg", "image/png"},
        "max_size_mb": 3,
        "max_resolution": (4000, 4000),
    },
    "state_id": {
        "mime_types": {"image/jpeg", "image/png"},
        "max_size_mb": 3,
        "max_resolution": (4000, 4000),
    },
    "ssn_card": {
        "mime_types": {"application/pdf", "image/jpeg", "image/png"},
        "max_size_mb": 2,
        "max_resolution": (3000, 3000),
    },
    "bank_statement": {
        "mime_types": {"application/pdf"},
        "max_size_mb": 10,
    },
    "pay_stub": {
        "mime_types": {"application/pdf"},
        "max_size_mb": 5,
    },
    "photo": {
        "mime_types": {"image/jpeg", "image/png"},
        "max_size_mb": 2,
        "max_resolution": (3000, 3000),
    },
    "w2": {
        "mime_types": {"application/pdf", "image/jpeg", "image/png"},
        "max_size_mb": 5,
        "max_resolution": (4000, 4000),
    },
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
        # -----------------------------
        # Basic validation (unchanged)
        # -----------------------------
        rules = self._validate_document_type(document_type)
        self._validate_mime_type(document_type, file, rules)

        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")

        self._validate_file_size(document_type, file_bytes, rules)
        self._validate_image_resolution_if_needed(
            document_type, file, file_bytes, rules
        )

        # -----------------------------
        # Temp file (passport only)
        # -----------------------------
        os.makedirs("temp_files", exist_ok=True)
        temp_upload = None

        if document_type == "passport":
            ext = os.path.splitext(file.filename)[1].lower()
            temp_upload = f"temp_files/upload_{uuid.uuid4().hex}{ext}"

            with open(temp_upload, "wb") as f:
                f.write(file_bytes)

            passport_ocr = PassportOCR()
            ocr_result = passport_ocr.process_file(
                temp_upload,
                document_type=document_type,
                application_id=application_id,
            )

            os.remove(temp_upload)

            if ocr_result["status"] != "success":
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Passport OCR failed: {ocr_result}",
                )
            os.remove(temp_upload)
            user_details = ocr_result["mrz_data"]
            print("[INFO] Extracted Passport MRZ Data:", user_details)
            
        # Specific validation for SSN Card
        if document_type == "ssn_card":
                validation_result = ssn_card_validation(temp_upload, document_type, application_id)
                if not validation_result["valid"]:
                    os.remove(temp_upload)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"SSN Card validation failed: {validation_result['doc_type']} (confidence: {validation_result['confidence']})",
                    )
                os.remove(temp_upload)
                print("Temp file deleted after SSN validation")  
        # -----------------------------
        # Image preprocessing (unchanged)
        # -----------------------------
        processed_bytes = file_bytes
        is_low_quality = False
        quality_scores = None

        if file.content_type.startswith("image/"):
            preprocessing_result = preprocess(file_bytes)
            processed_bytes = preprocessing_result.processed_image
            is_low_quality = preprocessing_result.is_low_quality
            quality_scores = preprocessing_result.quality_scores

        # -----------------------------
        # OCR + KEYWORD VALIDATION (CORE FIX)
        # -----------------------------
        ocr_result = extract_ocr(
            file_bytes=file_bytes,
            mime_type=file.content_type,
        )
        
        expected_type = DocumentType(document_type)

        is_valid, confidence = KeywordDocumentValidator.validate(
            expected_type=expected_type,
            ocr_text=ocr_result.full_text,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Uploaded document does not match expected type "
                    f"'{document_type}'. Please upload a valid {document_type}."
                ),
            )

        # -----------------------------
        # Persist ONLY AFTER validation
        # -----------------------------        if os.path.exists(temp_upload):
            os.remove(temp_upload)
            
        try:
            document = await self.dao.create_document(
                {
                    "id": uuid.uuid4(),
                    "application_id": uuid.UUID(application_id),

                    # SOURCE OF TRUTH = endpoint
                    "document_type": document_type,
                    "document_confidence": confidence,
                    "classification_method": "keyword_ocr",

                    "file_name": file.filename,
                    "mime_type": file.content_type,
                    "file_size": len(file_bytes),
                    "content": file_bytes,

                    "is_low_quality": is_low_quality,
                    "quality_metadata": quality_scores,
                }
            )

            await self.db.commit()
            await self.db.refresh(document)
            return document

        except SQLAlchemyError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while uploading document",
            )

    # -----------------------------
    # Validation helpers (UNCHANGED)
    # -----------------------------
    def _validate_document_type(self, document_type: str) -> dict:
        if document_type not in DOCUMENT_RULES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid document_type. "
                    f"Allowed values: {sorted(DOCUMENT_RULES.keys())}"
                ),
            )
        return DOCUMENT_RULES[document_type]

    def _validate_mime_type(
        self,
        document_type: str,
        file: UploadFile,
        rules: dict,
    ):
        if file.content_type not in rules["mime_types"]:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=(
                    f"Invalid MIME type '{file.content_type}' for {document_type}. "
                    f"Allowed types: {sorted(rules['mime_types'])}"
                ),
            )

    def _validate_file_size(
        self,
        document_type: str,
        file_bytes: bytes,
        rules: dict,
    ):
        max_size_bytes = rules["max_size_mb"] * 1024 * 1024
        if len(file_bytes) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"{document_type} exceeds maximum allowed size "
                    f"of {rules['max_size_mb']} MB"
                ),
            )

    def _validate_image_resolution_if_needed(
        self,
        document_type: str,
        file: UploadFile,
        file_bytes: bytes,
        rules: dict,
    ):
        if not file.content_type.startswith("image/"):
            return
        if "max_resolution" not in rules:
            return

        try:
            image = Image.open(BytesIO(file_bytes))
            width, height = image.size
            max_w, max_h = rules["max_resolution"]

            if width > max_w or height > max_h:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"{document_type} image resolution {width}x{height} exceeds "
                        f"maximum allowed {max_w}x{max_h}"
                    ),
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or corrupted image file",
            )
