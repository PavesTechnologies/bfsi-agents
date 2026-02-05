import os
import uuid
from io import BytesIO

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from PIL import Image

from src.repositories.intake_repo.document_upload_repo import LoanIntakeDAO
from src.domain.image_processing.preprocessor import preprocess

# Sprint 3 – Document Type Identification
from src.domain.document_classification.orchestrator import DocumentTypeIdentifier
from src.domain.document_classification.ml.layoutlm_classifier import LayoutLMClassifier
from src.domain.document_validation.ssn_card_doc_validation import ssn_card_validation
from src.domain.document_validation.aws_passport_validation import PassportOCR

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
    "visa": {
        "mime_types": {"application/pdf", "image/jpeg", "image/png"},
        "max_size_mb": 5,
        "max_resolution": (5000, 5000),
    },
    "i94": {
        "mime_types": {"application/pdf"},
        "max_size_mb": 2,
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
}


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = LoanIntakeDAO(db)

        # Sprint 3: document type identifier (rule-based + ML fallback)
        self.document_identifier = DocumentTypeIdentifier(
            ml_classifier=LayoutLMClassifier()
        )

    async def upload_document(
        self,
        application_id: str,
        document_type: str,
        file: UploadFile,
    ):
        # -----------------------------
        # Validation
        # -----------------------------
        rules = self._validate_document_type(document_type)
        self._validate_mime_type(document_type, file, rules)

        file_bytes = await file.read()
        
        if not file_bytes:
            raise HTTPException(400, "Empty file")

        self._validate_file_size(document_type, file_bytes, rules)
        self._validate_image_resolution_if_needed(
            document_type, file, file_bytes, rules
        )
        
        # ----------------------------
        # Create Temp Dir
        # ----------------------------
        os.makedirs("temp_files", exist_ok=True)

        ext = os.path.splitext(file.filename)[1].lower()

        temp_upload = f"temp_files/upload_{uuid.uuid4().hex}{ext}"
        
        print("[INFO] Saving temp upload to:", temp_upload)
        with open(temp_upload, "wb") as f:
            f.write(file_bytes)
        
        passport_ocr = PassportOCR()
        

        processed_bytes = file_bytes
        is_low_quality = False
        quality_scores = None

        if document_type == "passport":

            ocr_result = passport_ocr.process_file(
                temp_upload,
                document_type=document_type,
                application_id=application_id
            )

            if ocr_result["status"] != "success":
                os.remove(temp_upload)
                raise HTTPException(
                    400,
                    f"OCR failed: {ocr_result}"
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
        # Image preprocessing
        # -----------------------------
        if file.content_type.startswith("image/"):
            preprocessing_result = preprocess(file_bytes)

            processed_bytes = preprocessing_result.processed_image
            is_low_quality = preprocessing_result.is_low_quality
            quality_scores = preprocessing_result.quality_scores

        # -----------------------------
        # Sprint 3: Document Type Identification
        # -----------------------------
        document_classification = self.document_identifier.identify(
            file_bytes=file_bytes,
            mime_type=file.content_type,
        )
        
        if os.path.exists(temp_upload):
            os.remove(temp_upload)
            
        try:
            document = await self.dao.create_document(
                {
                    "id": uuid.uuid4(),
                    "application_id": uuid.UUID(application_id),

                    # Detected document metadata
                    "document_type": document_classification.document_type,
                    "document_confidence": document_classification.confidence,
                    "classification_method": document_classification.method,

                    # File metadata
                    "file_name": file.filename,
                    "mime_type": file.content_type,
                    "file_size": len(file_bytes),
                    "content": file_bytes,

                    # Quality metadata
                    "is_low_quality": is_low_quality,
                    "quality_metadata": quality_scores,
                }
            )

            await self.db.commit()
            await self.db.refresh(document)
            return document

        except SQLAlchemyError as exc:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while uploading document",
            )

    # -----------------------------
    # Validation helpers
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
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )

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
