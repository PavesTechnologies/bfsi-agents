# Future Features — Deferred from Sprint 1

## Hindi / Multilingual OCR Pipeline

**Deferred from:** Sprint 1 (1.4)
**Reason:** Deprioritised to reduce Sprint 1 scope; current AWS Textract OCR is sufficient for English-heavy Aadhaar/PAN/ITR documents. Hindi OCR is needed for fully vernacular documents (e.g., regional utility bills, Hindi-medium ITR copies).

---

### Design

#### Multi-Language OCR Dispatcher (`domain/ocr/multilingual_ocr.py`)

Three interchangeable engines selectable via config:

| Engine | Best For | Cost |
|--------|----------|------|
| **Google Cloud Vision** | Mixed Hindi+English docs, best accuracy | Paid |
| **Tesseract** | Offline/air-gapped, clean single-language docs | Free |
| **Bhashini (Dhruva API)** | Indic-script heavy, Govt-approved vendor | Govt API |

#### Language Detection Flow
1. Run quick Tesseract language detect on first page
2. If Devanagari script detected (`ऀ–ॿ` chars > 10%) → route to Hindi-capable engine
3. Otherwise → existing AWS Textract (English)

#### Implementation Skeleton

```python
# domain/ocr/multilingual_ocr.py
from enum import Enum

class OCREngine(Enum):
    GOOGLE_VISION = "google_vision"
    TESSERACT = "tesseract"
    BHASHINI = "bhashini"

class MultilingualOCR:
    def __init__(self, primary_engine: OCREngine = OCREngine.GOOGLE_VISION):
        self.primary = primary_engine

    async def extract_text(self, image_bytes: bytes, lang_hint: str = "auto") -> dict:
        if self.primary == OCREngine.GOOGLE_VISION:
            return await self._google_vision_ocr(image_bytes, lang_hint)
        elif self.primary == OCREngine.TESSERACT:
            return self._tesseract_ocr(image_bytes, lang_hint)
        elif self.primary == OCREngine.BHASHINI:
            return await self._bhashini_ocr(image_bytes, lang_hint)

    async def _google_vision_ocr(self, image_bytes: bytes, lang_hint: str) -> dict:
        from google.cloud import vision
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        hints = vision.ImageContext(
            language_hints=["hi", "en"] if lang_hint == "auto" else [lang_hint]
        )
        response = client.document_text_detection(image=image, image_context=hints)
        full_text = response.full_text_annotation.text if response.full_text_annotation else ""
        detected_langs = [
            {"lang": lang.language_code, "confidence": lang.confidence}
            for page in response.full_text_annotation.pages
            for lang in page.property.detected_languages
        ]
        return {"full_text": full_text, "detected_languages": detected_langs, "engine": "google_vision"}

    def _tesseract_ocr(self, image_bytes: bytes, lang_hint: str) -> dict:
        import pytesseract
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        lang_code = "hin+eng" if lang_hint in ("auto", "hi") else "eng"
        text = pytesseract.image_to_string(img, lang=lang_code)
        return {"full_text": text, "detected_languages": [{"lang": lang_code}], "engine": "tesseract"}

    async def _bhashini_ocr(self, image_bytes: bytes, lang_hint: str) -> dict:
        import httpx, base64
        payload = {
            "pipelineTasks": [{"taskType": "ocr", "config": {"language": {"sourceLanguage": "hi"}}}],
            "inputData": {"image": [{"imageContent": base64.b64encode(image_bytes).decode()}]}
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://dhruva-api.bhashini.gov.in/services/inference/pipeline",
                json=payload,
                headers={"Authorization": "Bearer <BHASHINI_API_KEY>"}
            )
        result = resp.json()
        return {
            "full_text": result.get("output", [{}])[0].get("source", ""),
            "engine": "bhashini"
        }
```

#### Integration Points
- `ocr_dispatcher.py` — add language detection branch before routing to AWS Textract
- `document_upload_service.py` — pass `lang_hint` from `preferred_language` on applicant record
- New env vars needed: `GOOGLE_APPLICATION_CREDENTIALS`, `BHASHINI_API_KEY`
- New pip deps: `google-cloud-vision`, `pytesseract`, `Pillow` (already present)

#### Testing Plan
- Unit: synthetic Hindi text through Tesseract engine
- Integration: real Aadhaar scan with Devanagari address field → Google Vision
- Regression: existing English-only docs still route to AWS Textract

#### When to Implement
- When > 15% of uploaded docs are failing OCR extraction (monitor `document_confidence < 0.5`)
- Before any regional language market expansion (Tamil, Telugu, Bengali states)

---

## Aadhaar / PAN / Voter ID — Cross-Validation & Normalisation

**Deferred from:** Sprint 1 (`_process_and_store_document` in `document_upload_service.py`)
**Blocked on:** Confirming third-party vendor / government API for structured data extraction from each document.

### Context

Passport and Driver's License already follow a complete pipeline:
```
OCR → normalize structured fields → CrossValidationService → reject on mismatch
```
Aadhaar, PAN, and Voter ID currently stop after keyword-based OCR validation. They need the same treatment but require a confirmed source to extract structured fields reliably.

---

### Aadhaar

**Blocked on:** Confirming barcode / QR decoder source (UIDAI offline XML or third-party SDK).

**Options:**
| Source | Method | Structured Output |
|--------|--------|------------------|
| UIDAI Offline XML | Scan secure QR on Aadhaar → decrypt XML | Name, DOB, Gender, Address, masked Aadhaar no. |
| DigiLocker API | OAuth pull | Same fields, verified by UIDAI |
| Third-party SDK (e.g. HyperVerge, IDfy) | API call with image bytes | Name, DOB, Address, Aadhaar no. |

**Implementation (once vendor confirmed):**
```python
# in _process_and_store_document, after keyword OCR validation
if document_type == "aadhaar_card":
    aadhaar_data = aadhaar_scanner.extract(temp_path)          # vendor SDK
    normalizer = AadhaarNormalizer()
    normalized = normalizer.normalize(aadhaar_data)
    cross_result = await CrossValidationService(...).validate_aadhaar(
        application_id, normalized
    )
    if not cross_result.valid:
        raise HTTPException(400, {"mismatches": cross_result.mismatches})
    confidence = aadhaar_data.get("confidence", confidence)
```

---

### PAN Card

**Blocked on:** Confirming NSDL / UTI scan API access or third-party PAN scanner vendor.

**Options:**
| Source | Method | Structured Output |
|--------|--------|------------------|
| NSDL PAN Verify API | PAN no. + DOB lookup | Name, Status, DOB |
| UTI Infrastructure API | Same | Name, Status |
| Third-party SDK (HyperVerge, Karza) | Image scan | Name, DOB, Father's Name, PAN no. |

**Implementation:**
```python
if document_type == "pan_card":
    pan_data = pan_scanner.extract(temp_path)                  # vendor SDK
    normalizer = PANNormalizer()
    normalized = normalizer.normalize(pan_data)
    cross_result = await CrossValidationService(...).validate_pan(
        application_id, normalized
    )
    if not cross_result.valid:
        raise HTTPException(400, {"mismatches": cross_result.mismatches})
```

---

### Voter ID (EPIC)

**Blocked on:** Confirming ECI EPIC API access or third-party Voter ID scanner vendor.

**Options:**
| Source | Method | Structured Output |
|--------|--------|------------------|
| ECI Voter Portal API | EPIC no. lookup | Name, Father's Name, Address, Part no. |
| Third-party SDK (HyperVerge, IDfy) | Image scan | Name, Address, EPIC no. |

**Implementation:**
```python
if document_type == "voter_id":
    voter_data = voter_id_scanner.extract(temp_path)           # vendor SDK
    normalizer = VoterIDNormalizer()
    normalized = normalizer.normalize(voter_data)
    cross_result = await CrossValidationService(...).validate_voter_id(
        application_id, normalized
    )
    if not cross_result.valid:
        raise HTTPException(400, {"mismatches": cross_result.mismatches})
```

---

### Files to Create (once unblocked)
| File | Purpose |
|------|---------|
| `domain/normalization/aadhaar.py` | `AadhaarNormalizer` — maps vendor fields → internal schema |
| `domain/normalization/pan.py` | `PANNormalizer` |
| `domain/normalization/voter_id.py` | `VoterIDNormalizer` |
| `services/cross_validation_service.py` | Add `validate_aadhaar`, `validate_pan`, `validate_voter_id` methods |

### When to Implement
- After vendor / API contract is signed
- Before KYC Agent Sprint 2 (which depends on verified identity fields from Intake)

---

## Configurable Document Requirements (Lender-Specific)

**Deferred from:** Sprint 1 (Document Readiness Gate)  
**Reason:** Initial MVP uses hardcoded mandatory docs + required groups for all lenders. Multi-lender support requires database-backed configuration.

### Context

Currently, `DocumentReadinessChecker` enforces a fixed set of document requirements:
```python
MANDATORY_DOCS = ["aadhaar_card", "pan_card", "photo"]
REQUIRED_GROUPS = {
    "income_proof": ["salary_slip", "form_16", "itr"],
    "address_proof": ["utility_bill", "voter_id", ...],
    "bank_proof": ["bank_statement"],
}
```

Different banks/lenders have different KYC policies. For example:
- **NBFC A** may require: Aadhaar + PAN + Form 16 (income + identity only)
- **Bank B** may require: Aadhaar + PAN + Salary Slip + Bank Statement + Photo + Address Proof (stricter)
- **Fintech C** may only require: Aadhaar + Photo (lighter verification)

### Design

#### 1. Database Schema

```sql
CREATE TABLE lender_document_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lender_id UUID NOT NULL REFERENCES loan_application(lender_id),
    
    -- JSON array of mandatory doc types (e.g., ["aadhaar_card", "pan_card"])
    mandatory_documents JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- JSON object: group_name → array of accepted doc types
    -- e.g., {"income_proof": ["salary_slip", "form_16"], "address_proof": [...]}
    required_groups JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by UUID REFERENCES applicant(id),
    
    UNIQUE(lender_id)
);

CREATE INDEX idx_lender_doc_req ON lender_document_requirements(lender_id);
```

#### 2. Service Layer

```python
# services/document_requirements_service.py

class DocumentRequirementsService:
    async def get_requirements_for_lender(self, lender_id: UUID) -> DocumentRequirements:
        """Fetch lender-specific or fallback to defaults."""
        # Fetch from DB; if not found, return HARDCODED_DEFAULTS
        
    async def update_lender_requirements(
        self,
        lender_id: UUID,
        mandatory_docs: list[str],
        required_groups: dict[str, list[str]],
    ) -> DocumentRequirements:
        """Update requirements for a lender (admin-only endpoint)."""
```

#### 3. Updated Readiness Checker

```python
# services/document_readiness.py (updated)

class DocumentReadinessChecker:
    def __init__(self, db: AsyncSession, lender_id: UUID):
        self.dao = LoanIntakeDAO(db)
        self.req_service = DocumentRequirementsService(db)
        self.lender_id = lender_id

    async def check(self, application_id: UUID) -> ReadinessResult:
        # Fetch lender's requirements (or defaults if not configured)
        requirements = await self.req_service.get_requirements_for_lender(self.lender_id)
        
        uploaded = await self.dao.get_uploaded_document_types(application_id)
        
        # Validate using lender-specific rules (instead of global MANDATORY_DOCS / REQUIRED_GROUPS)
        missing_mandatory = [d for d in requirements.mandatory_docs if d not in uploaded]
        # ... rest of logic same
```

#### 4. Admin API

```python
# api/v1/admin_routes/lender_config_routes.py

@router.post("/admin/lenders/{lender_id}/document-requirements", dependencies=[Depends(require_admin)])
async def set_document_requirements(
    lender_id: UUID,
    req: SetDocumentRequirementsRequest,  # { mandatory: [...], groups: {...} }
    db: AsyncSession = Depends(get_db),
):
    """Bank admin configures document requirements for their org."""
    service = DocumentRequirementsService(db)
    return await service.update_lender_requirements(lender_id, req.mandatory, req.groups)

@router.get("/admin/lenders/{lender_id}/document-requirements")
async def get_document_requirements(
    lender_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch current requirements."""
    service = DocumentRequirementsService(db)
    return await service.get_requirements_for_lender(lender_id)
```

#### 5. UI Component (Lender Dashboard)

- Checkbox list for **Mandatory Documents** — toggle each doc type required for all applications
- **Required Groups** section — add/remove groups, drag-and-drop doc types into groups
- Validation: at least 1 mandatory doc, at least 1 doc per group
- Preview: "Example checklist for applicants" showing what will be required

#### 6. Integration Points

- **trigger_orchestrator**: Query lender_id from application, pass to `DocumentReadinessChecker(db, lender_id)`
- **document_upload_routes**: No change — upload is pre-readiness; readiness check happens at trigger time
- **Fallback strategy**: If lender has no configured requirements, use `HARDCODED_DEFAULTS`

### Files to Create / Modify

| File | Change |
|------|--------|
| `models/models.py` | Add `LenderDocumentRequirements` model + relation to `LoanApplication` |
| `repositories/lender_config_repo.py` | DAO for CRUD on document requirements |
| `services/document_requirements_service.py` | Fetch, validate, update lender requirements |
| `services/document_readiness.py` | Accept `lender_id`, use dynamic requirements instead of globals |
| `api/v1/admin_routes/lender_config_routes.py` | Admin endpoints to configure per-lender requirements |
| Update `trigger_orchestrator` | Extract `lender_id` from application, pass to checker |

### When to Implement

- After initial multi-lender support is added to the platform
- Before onboarding new lenders with custom KYC policies
- Timeline: Sprint 2 or later
