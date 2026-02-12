import os
import uuid
from io import BytesIO
from uuid import UUID

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from PIL import Image

from src.repositories.intake_repo.address_repo import AddressDAO
from src.repositories.intake_repo.applicant_repo import ApplicantDAO
from src.services.idempotency_guard import IdempotencyGuard
from src.repositories.idempotency_repository import IdempotencyRepository
from src.utils.hash import stable_bytes_hash

from src.repositories.intake_repo.document_upload_repo import LoanIntakeDAO
from src.domain.image_processing.preprocessor import preprocess

# Keep existing special validations
from src.domain.document_validation.ssn_card_doc_validation import ssn_card_validation
from src.domain.document_validation.aws_passport_validation import PassportOCR
from src.domain.document_validation.usa_driving_licence_validation import process_single_dl

# OCR (AWS Textract ONLY)
from src.domain.ocr.ocr_dispatcher import extract_ocr

# Keyword-based intent validation
from src.domain.document_validation.keyword_document_validator import (
    KeywordDocumentValidator,
)
from src.domain.document_classification.document_type import DocumentType

from src.domain.normalization.drivers_license import DriversLicenseNormalizer
from src.domain.normalization.passport import PassportNormalizer

from src.services.cross_validation_service import CrossValidationService



# -----------------------------
# Document rules (UNCHANGED)
# -----------------------------
DOCUMENT_RULES = {
    "passport": {
        "mime_types": {"application/pdf", "image/jpeg", "image/png","image/jpg"},
        "max_size_mb": 5,
        "max_resolution": (5000, 5000),
    },
    "drivers_license": {
        "mime_types": {"image/jpeg", "image/png","image/jpg"},
        "max_size_mb": 3,
        "max_resolution": (4000, 4000),
    },
    "state_id": {
        "mime_types": {"image/jpeg", "image/png","image/jpg"},
        "max_size_mb": 3,
        "max_resolution": (4000, 4000),
    },

    "ssn_card": {
        "mime_types": {"application/pdf", "image/jpeg", "image/png","image/jpg"},
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
        "mime_types": {"image/jpeg", "image/png","image/jpg"},
        "max_size_mb": 2,
        "max_resolution": (3000, 3000),
    },
    "w2": {
        "mime_types": {"application/pdf", "image/jpeg", "image/png","image/jpg"},
        "max_size_mb": 5,
        "max_resolution": (4000, 4000),
    },
}


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = LoanIntakeDAO(db)
        self.applicant_dao = ApplicantDAO(db)
        self.address_dao = AddressDAO(db)

    # =========================================================
    # PUBLIC API — IDEMPOTENT WRAPPER (ADDED)
    # =========================================================
    async def upload_document(
        self,
        application_id: str,
        document_type: str,
        file: UploadFile,
    ):
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )

        # -----------------------------
        # 🔐 DOCUMENT IDEMPOTENCY KEY
        # -----------------------------
        document_hash = stable_bytes_hash(file_bytes)

        synthetic_request_id = UUID(
            stable_bytes_hash(
                f"{application_id}:{document_type}:{document_hash}".encode()
            )[:32]
        )

        guard = IdempotencyGuard(
            repo=IdempotencyRepository(self.db)
        )

        async def first_execution():
            try:
                return await self._process_and_store_document(
                    application_id=application_id,
                    document_type=document_type,
                    file=file,
                    file_bytes=file_bytes,
                    synthetic_request_id=synthetic_request_id,
                )
            except HTTPException as e:
                await IdempotencyRepository(self.db).delete(synthetic_request_id)
                raise e
            except Exception as e:
                # For unexpected crashes, we also want to allow a retry
                await IdempotencyRepository(self.db).delete(synthetic_request_id)
                raise e

        return await guard.execute(
            request_id=synthetic_request_id,
            app_id=application_id,
            payload={
                "application_id": application_id,
                "document_type": document_type,
                "file_hash": document_hash,
            },
            on_first_execution=first_execution,
        )

    # =========================================================
    # ORIGINAL LOGIC — MOVED VERBATIM (UNCHANGED)
    # =========================================================
    async def _process_and_store_document(
        self,
        application_id: str,
        document_type: str,
        file: UploadFile,
        file_bytes: bytes,
        synthetic_request_id: uuid.UUID,
    ):
        temp_path = None

        
        try:
            # -----------------------------
            # Basic validation
            # -----------------------------
            rules = self._validate_document_type(document_type)
            self._validate_mime_type(document_type, file, rules)

            self._validate_file_size(document_type, file_bytes, rules)
            self._validate_image_resolution_if_needed(
                document_type, file, file_bytes, rules
            )

            # -----------------------------
            # Temp directory
            # -----------------------------
            os.makedirs("temp_files", exist_ok=True)
            ext = os.path.splitext(file.filename)[1].lower()
            temp_path = f"temp_files/upload_{uuid.uuid4().hex}{ext}"

            with open(temp_path, "wb") as f:
                f.write(file_bytes)

            # -----------------------------
            # Driver's License validation
            # -----------------------------
            if document_type == "drivers_license":
                validation_result = await process_single_dl(application_id,temp_path , self.applicant_dao, self.address_dao)
                confidence = validation_result.get("confidence_score", 0)
                
                os.remove(temp_path)
                if not validation_result.get("valid", False):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "message": "Driver's License validation failed",
                            "reason_code": validation_result.get("doc_type", "UNKNOWN"),
                            "confidence_score": confidence,
                            "mismatches": validation_result.get("cross_validation_mismatches", [])
                        }
                    )

            # -----------------------------
            # Passport MRZ validation
            # -----------------------------
            if document_type == "passport":
                passport_ocr = PassportOCR()
                result = passport_ocr.process_file(
                    temp_path,
                    document_type=document_type,
                    application_id=application_id,
                )
                confidence = result.get("confidence", 0)
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if result["status"] != "success":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Passport MRZ validation failed",
                    )

            # -----------------------------
            # Image preprocessing (quality only)
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
            # SSN Card validation
            # -----------------------------
            if document_type == "ssn_card":
                validation_result = ssn_card_validation(
                    temp_path,
                    "ssn_card",
                    application_id
                    )
                # print(f"SSN Card validation result: {validation_result}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                confidence = validation_result.get("confidence", 0)

            if not validation_result["valid"]:
                raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                f"SSN Card validation failed: "
                f"{validation_result['doc_type']} "
                f"(confidence: {validation_result['confidence']})"
            ),
        )
           
            # -----------------------------
            # OCR + KEYWORD INTENT VALIDATION
            # -----------------------------
            if document_type not in ["passport", "ssn_card", "drivers_license"]:
                ocr_result = extract_ocr(
                    file_bytes=file_bytes,
                    mime_type=file.content_type,
                )
                
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
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
            # Persist ONLY AFTER ALL VALIDATIONS
            # -----------------------------
            
            # Ensure all required fields are present and valid
            required_fields = {
                "application_id": uuid.UUID(application_id),
                "document_type": document_type,
                "file_name": file.filename,
                "mime_type": file.content_type,
                "file_size": len(file_bytes),
                "content": processed_bytes,
                "is_low_quality": is_low_quality if is_low_quality is not None else False,
            }
            for k, v in required_fields.items():
                if v is None:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {k}")
            document_data = {
                **required_fields,
                "document_confidence": confidence,
                "classification_method": "keyword_ocr",
                "quality_metadata": quality_scores,
            }
            document = await self.dao.create_document(document_data)
            await self.db.commit()
            await self.db.refresh(document)

            # Serialize document to dict for idempotency
            response_payload = {
                "id": str(getattr(document, "id", None)),
                "file_name": getattr(document, "file_name", None),
                "mime_type": getattr(document, "mime_type", None),
                "file_size": getattr(document, "file_size", None),
                "document_type": getattr(document, "document_type", None),
                "document_confidence": getattr(document, "document_confidence", None),
                "classification_method": getattr(document, "classification_method", None),
                "is_low_quality": getattr(document, "is_low_quality", None),
                "quality_metadata": getattr(document, "quality_metadata", None),
            }
            # Mark idempotency as completed
            # Use the synthetic_request_id (idempotency key) for marking completed
            await IdempotencyRepository(self.db).mark_completed(request_id=synthetic_request_id, response_payload=response_payload)
            return document

        except SQLAlchemyError as e:
            await self.db.rollback()
            print(f"DATABASE ERROR: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while uploading document",
            )

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

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
