# Sprint 1: Intake Agent — India Adaptation (2 Weeks)

## 1.1 Data Model Changes

### Applicant Model (`models/models.py`)

```diff
# REMOVE USA-specific fields
- ssn_encrypted: Mapped[Optional[str]] = mapped_column(Text)
- ssn_last4: Mapped[Optional[str]] = mapped_column(CHAR(4))
- itin_number: Mapped[Optional[str]] = mapped_column(String(15))
- citizenship_status: Mapped[Optional[str]] = mapped_column(String(30))
- suffix: Mapped[Optional[str]] = mapped_column(String(10))

# ADD India-specific fields
+ aadhaar_encrypted: Mapped[Optional[str]] = mapped_column(Text)  # AES-256 encrypted
+ aadhaar_last4: Mapped[Optional[str]] = mapped_column(CHAR(4))
+ aadhaar_vid: Mapped[Optional[str]] = mapped_column(String(16))  # Virtual ID
+ pan_number: Mapped[Optional[str]] = mapped_column(String(10))  # ABCDE1234F
+ pan_verified: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
+ father_name: Mapped[Optional[str]] = mapped_column(String(100))  # Common in Indian docs
+ mother_name: Mapped[Optional[str]] = mapped_column(String(100))
+ ckyc_number: Mapped[Optional[str]] = mapped_column(String(14))  # CKYC registry
+ preferred_language: Mapped[Optional[str]] = mapped_column(String(10), default="en")
```

### Address Model
```diff
- state: Mapped[str] = mapped_column(String(30))  # US 2-letter code
- zip_code: Mapped[str] = mapped_column(String(10))  # 5 or 9 digit
- country: ... server_default=text("'USA'")

+ state: Mapped[str] = mapped_column(String(50))  # Full Indian state name
+ pin_code: Mapped[str] = mapped_column(String(6))  # 6-digit PIN
+ district: Mapped[Optional[str]] = mapped_column(String(100))
+ country: ... server_default=text("'INDIA'")
```

### PgsqlDocument — Document Types
```diff
# REMOVE USA types
- 'ssn_card', 'drivers_license', 'state_id', 'w2', 'pay_stub', 'tax_return'

# ADD India types
+ 'aadhaar_card', 'pan_card', 'voter_id', 'driving_license_india',
+ 'passport_india', 'bank_statement', 'itr', 'form_16',
+ 'salary_slip', 'utility_bill', 'photo', 'address_proof',
+ 'gst_certificate', 'udyam_certificate'
```

---

## 1.2 Indian Documents — Capture & Validation

### Document Matrix

| Document | Purpose | Validation Method | OCR Fields to Extract |
|----------|---------|-------------------|----------------------|
| **Aadhaar Card** | Identity + Address | Verhoeff checksum on 12-digit number, QR decode, UIDAI API verify | Name, DOB, Gender, Address, Aadhaar No |
| **PAN Card** | Tax Identity | Regex `[A-Z]{5}[0-9]{4}[A-Z]`, NSDL/UTI API verify | Name, DOB, PAN No, Father's Name |
| **Voter ID (EPIC)** | Identity + Address | Regex `[A-Z]{3}[0-9]{7}`, ECI API verify | Name, Father's Name, Address, EPIC No |
| **Driving License** | Identity + Address | Format varies by state, Vahan/Sarathi API | Name, DOB, DL No, Validity, Address |
| **Passport** | Identity | MRZ parsing (existing), MEA database | Name, DOB, Passport No, Validity |
| **Bank Statement** | Income Proof | PDF parsing + AI extraction | Account No, IFSC, Transactions, Balance |
| **ITR / Form 16** | Income Proof | PAN cross-ref, ITR-V XML parse | Gross Income, Tax Paid, Assessment Year |
| **Salary Slip** | Income Proof | OCR + employer name match | Gross, Net, Deductions, Month |
| **Utility Bill** | Address Proof | Date validation (< 3 months old) | Name, Address, Bill Date |

### Aadhaar Validation Implementation

```python
# domain/document_validation/aadhaar_validation.py

VERHOEFF_TABLE_D = [
    [0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],
    [2,3,4,0,1,7,8,9,5,6],[3,4,0,1,2,8,9,5,6,7],
    [4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],
    [8,7,6,5,9,3,2,1,0,4],[9,8,7,6,5,4,3,2,1,0]
]
VERHOEFF_TABLE_P = [
    [0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],
    [5,8,0,3,7,9,6,1,4,2],[8,9,1,6,0,4,3,5,2,7],
    [9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8]
]
VERHOEFF_TABLE_INV = [0,4,3,2,1,5,6,7,8,9]

def validate_aadhaar_checksum(aadhaar: str) -> bool:
    """Validate Aadhaar using Verhoeff algorithm."""
    digits = [int(d) for d in aadhaar.strip().replace(" ", "")]
    if len(digits) != 12:
        return False
    c = 0
    for i, digit in enumerate(reversed(digits)):
        c = VERHOEFF_TABLE_D[c][VERHOEFF_TABLE_P[i % 8][digit]]
    return c == 0

def validate_aadhaar(text: str) -> dict:
    """Full Aadhaar card validation from OCR text."""
    import re
    aadhaar_match = re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', text)
    aadhaar_number = aadhaar_match.group().replace(" ", "") if aadhaar_match else None

    keywords = ["government of india", "unique identification", "uidai", "aadhaar"]
    has_keywords = any(k in text.lower() for k in keywords)
    checksum_valid = validate_aadhaar_checksum(aadhaar_number) if aadhaar_number else False

    confidence = 0.0
    if aadhaar_number: confidence += 0.4
    if has_keywords: confidence += 0.3
    if checksum_valid: confidence += 0.3

    return {
        "doc_type": "AADHAAR" if confidence >= 0.7 else "INVALID",
        "valid": checksum_valid and has_keywords,
        "confidence": round(confidence, 3),
        "aadhaar_number": aadhaar_number,
        "checksum_valid": checksum_valid,
    }
```

### PAN Validation
```python
# domain/document_validation/pan_validation.py
import re

PAN_REGEX = re.compile(r'^[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]$')
# 4th char: A=AOP, B=BOI, C=Company, F=Firm, G=Govt, H=HUF, J=AJP, L=Local, P=Person, T=Trust

def validate_pan(text: str) -> dict:
    pan_match = re.search(r'[A-Z]{5}\d{4}[A-Z]', text.upper())
    pan_number = pan_match.group() if pan_match else None

    keywords = ["income tax", "permanent account number", "govt. of india"]
    has_keywords = any(k in text.lower() for k in keywords)
    format_valid = bool(PAN_REGEX.match(pan_number)) if pan_number else False

    return {
        "doc_type": "PAN" if format_valid else "INVALID",
        "valid": format_valid and has_keywords,
        "pan_number": pan_number,
        "pan_type": _pan_entity_type(pan_number) if pan_number else None,
    }

def _pan_entity_type(pan: str) -> str:
    mapping = {"P": "Individual", "C": "Company", "H": "HUF", "F": "Firm", "T": "Trust"}
    return mapping.get(pan[3], "Other")
```

---

## 1.3 ZIP File Upload & Extraction

### New Endpoint + Service

```python
# api/routes.py — NEW endpoint
@router.post("/upload-documents-zip/{application_id}")
async def upload_documents_zip(application_id: str, file: UploadFile = File(...)):
    """Accept a ZIP file, extract all documents, classify and validate each."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files accepted")
    if file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(413, "ZIP file exceeds 50MB limit")
    return await zip_processor.process_zip(application_id, await file.read())
```

```python
# services/zip_processor.py
import zipfile, io, mimetypes
from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"}
MAX_FILES_PER_ZIP = 20

class ZipProcessor:
    async def process_zip(self, application_id: str, zip_bytes: bytes) -> dict:
        results = []
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            entries = [e for e in zf.namelist() if not e.startswith("__MACOSX")]
            if len(entries) > MAX_FILES_PER_ZIP:
                raise ValueError(f"Too many files ({len(entries)}). Max: {MAX_FILES_PER_ZIP}")

            for entry in entries:
                ext = Path(entry).suffix.lower()
                if ext not in ALLOWED_EXTENSIONS:
                    results.append({"file": entry, "status": "SKIPPED", "reason": f"Unsupported: {ext}"})
                    continue

                file_bytes = zf.read(entry)
                mime = mimetypes.guess_type(entry)[0] or "application/octet-stream"

                # Step 1: Classify document type (ML + rule-based)
                doc_type = await self.classify_document(file_bytes, mime)

                # Step 2: Run OCR (with language detection)
                ocr_result = await self.run_ocr(file_bytes, mime)

                # Step 3: Validate based on classified type
                validation = await self.validate_document(doc_type, ocr_result, file_bytes)

                # Step 4: Store in PgsqlDocument
                await self.store_document(application_id, entry, file_bytes, mime, doc_type, validation)

                results.append({
                    "file": entry, "doc_type": doc_type,
                    "validation": validation, "status": "PROCESSED"
                })
        return {"application_id": application_id, "documents": results}
```

---

## 1.4 Hindi OCR Pipeline

### Multi-Language OCR Dispatcher

```python
# domain/ocr/multilingual_ocr.py
from enum import Enum

class OCREngine(Enum):
    GOOGLE_VISION = "google_vision"
    TESSERACT = "tesseract"
    BHASHINI = "bhashini"

class MultilingualOCR:
    """OCR dispatcher supporting English + Hindi (Devanagari)."""

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
        """Google Cloud Vision — best accuracy for Hindi + English mixed docs."""
        from google.cloud import vision
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)

        hints = vision.ImageContext(language_hints=["hi", "en"] if lang_hint == "auto" else [lang_hint])
        response = client.document_text_detection(image=image, image_context=hints)

        full_text = response.full_text_annotation.text if response.full_text_annotation else ""
        detected_langs = []
        for page in response.full_text_annotation.pages:
            for lang in page.property.detected_languages:
                detected_langs.append({"lang": lang.language_code, "confidence": lang.confidence})

        return {"full_text": full_text, "detected_languages": detected_langs, "engine": "google_vision"}

    def _tesseract_ocr(self, image_bytes: bytes, lang_hint: str) -> dict:
        """Tesseract — offline, free, good for clean documents."""
        import pytesseract
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        lang_code = "hin+eng" if lang_hint in ("auto", "hi") else "eng"
        text = pytesseract.image_to_string(img, lang=lang_code)
        return {"full_text": text, "detected_languages": [{"lang": lang_code}], "engine": "tesseract"}

    async def _bhashini_ocr(self, image_bytes: bytes, lang_hint: str) -> dict:
        """Bhashini — Indian govt API, optimized for Indic scripts."""
        import httpx, base64
        payload = {
            "pipelineTasks": [{"taskType": "ocr", "config": {"language": {"sourceLanguage": "hi"}}}],
            "inputData": {"image": [{"imageContent": base64.b64encode(image_bytes).decode()}]}
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://dhruva-api.bhashini.gov.in/services/inference/pipeline", json=payload)
            result = resp.json()
        return {"full_text": result.get("output", [{}])[0].get("source", ""), "engine": "bhashini"}
```

---

## 1.5 Field Validator Changes (`validation/constants.py`)

```diff
# REMOVE USA
- PHONE_REGEX = re.compile(r"^\+1\d{10}$")
- SSN_REGEX = re.compile(r"^\d{3}-\d{2}-\d{4}$")
- SSN_LAST4_REGEX = re.compile(r"^\d{4}$")
- ZIP_REGEX = re.compile(r"^\d{5}(-\d{4})?$")
- STATE_CODES = {"AL", "AK", "AZ", ...}

# ADD India
+ PHONE_REGEX = re.compile(r"^\+91[6-9]\d{9}$")
+ AADHAAR_REGEX = re.compile(r"^\d{12}$")
+ AADHAAR_LAST4_REGEX = re.compile(r"^\d{4}$")
+ PAN_REGEX = re.compile(r"^[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]$")
+ PINCODE_REGEX = re.compile(r"^[1-9]\d{5}$")
+ IFSC_REGEX = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
+ INDIAN_STATE_CODES = {
+     "AN","AP","AR","AS","BR","CG","CH","DD","DL","GA","GJ","HP","HR",
+     "JH","JK","KA","KL","LA","LD","MH","ML","MN","MP","MZ","NL",
+     "OD","PB","PY","RJ","SK","TN","TS","TR","UK","UP","WB",
+ }
+ NAME_REGEX = re.compile(r"^[A-Za-z\u0900-\u097F\s\-'\.]{1,100}$")  # Supports Devanagari
```
