import os
import re
from datetime import date

import boto3
from dynamsoft_barcode_reader_bundle import (
    EnumBarcodeFormat,
    EnumErrorCode,
    EnumPresetTemplate,
    LicenseManager,
    CaptureVisionRouter,
)
from src.core.config import get_settings
from src.domain.normalization.drivers_license import DriversLicenseNormalizer
from src.services.cross_validation_service import CrossValidationService

settings = get_settings()
LICENSE_KEY = settings.BARCODE_LICENSE_KEY

BUCKET_NAME = "ajay-ocr-bucket-12345"
REGION = "us-east-1"

s3_client = boto3.client("s3", region_name=REGION)

# --- 1. AAMVA CONFIGURATION & PARSING ---
AAMVA_FIELDS = {
    "DCS": "last_name",
    "DAC": "first_name",
    "DAD": "middle_name",
    "DBB": "date_of_birth",
    "DBC": "sex",
    "DBA": "expiry_date",
    "DBD": "issue_date",
    "DAQ": "license_number",
    "DCG": "country",
    "DAG": "street_address",
    "DAI": "city",
    "DAJ": "state",
    "DAK": "postal_code",
}

REQUIRED_FIELDS = [
    "license_number",
    "first_name",
    "last_name",
    "date_of_birth",
    "expiry_date",
    "state",
]
OPTIONAL_FIELDS = ["issue_date", "street_address", "city", "postal_code", "sex"]


def upload_to_s3(local_path: str, application_id: str) -> str:
    try:
        # Extract file extension (.jpg, .png, etc.)
        _, ext = os.path.splitext(local_path)

        if not ext:
            raise ValueError("File has no extension")

        s3_key = f"drivers_license/_drivers_license_{application_id}{ext.lower()}"

        s3_client.upload_file(local_path, BUCKET_NAME, s3_key)

        print(f"✅ Uploaded to S3: {s3_key}")
        return s3_key

    except Exception as e:
        print(f"❌ S3 Upload failed: {e}")
        return None


def parse_aamva_payload(payload: str) -> dict:
    data = {}
    for code, field in AAMVA_FIELDS.items():
        # Match the code and grab everything until the next newline or carriage return
        match = re.search(rf"{code}([^\n\r]+)", payload)
        if match:
            data[field] = match.group(1).strip()
        # print(f"Extracted {field}: {data.get(field, 'N/A')}")
    return data


# def normalize_dl_data(data: dict) -> dict:
#     def parse_date(value):
#         # Common AAMVA date formats: MMDDYYYY or YYYYMMDD
#         for fmt in ("%m%d%Y", "%Y%m%d"):
#             try:
#                 return datetime.strptime(value, fmt).date().isoformat()
#             except: continue
#         return value

#     for field in ["date_of_birth", "expiry_date", "issue_date"]:
#         if field in data:
#             data[field] = parse_date(data[field])
#     return data


def validate_dl(data: dict) -> dict:
    present_req = [f for f in REQUIRED_FIELDS if f in data]
    print(f"Present required fields: {present_req} / {REQUIRED_FIELDS}")
    req_score = len(present_req) / len(REQUIRED_FIELDS)

    is_expired = False
    if "expiry_date" in data:
        try:
            is_expired = date.fromisoformat(data["expiry_date"]) < date.today()
        except ValueError:
            pass

    is_valid = req_score >= 0.8 and not is_expired

    return {
        "doc_type": "DRIVERS_LICENSE" if is_valid else "INVALID",
        "valid": is_valid,
        "expired": is_expired,
        "confidence_score": round(req_score, 2),
        "extracted_fields": data,
    }


# --- 2. DYNAMSOFT INTEGRATION ---
LicenseManager.init_license(LICENSE_KEY)  # noqa: F821
router = CaptureVisionRouter()  # noqa: F821


async def process_single_dl(
    application_id: str, image_path: str, applicant_dao=None, address_dao=None
):
    print(f"🚀 Processing: {os.path.basename(image_path)}")

    # Use Dynamsoft to capture barcodes
    result = router.capture(image_path, EnumPresetTemplate.PT_READ_BARCODES)  # noqa: F405

    if result.get_error_code() != EnumErrorCode.EC_OK:  # noqa: F405
        return {"error": result.get_error_string(), "valid": False}

    items = result.get_items()
    for item in items:
        # Filter for PDF417
        if item.get_format() == EnumBarcodeFormat.BF_PDF417:  # noqa: F405
            raw_payload = item.get_text()

            # Run your existing logic chain
            parsed = parse_aamva_payload(raw_payload)
            # normalized = normalize_dl_data(parsed)
            print(f"Parsed Data: {parsed}")
            normalizer = DriversLicenseNormalizer()
            validation_result = validate_dl(parsed)

            if validation_result["valid"]:
                s3_path = upload_to_s3(image_path, application_id)
                validation_result["s3_path"] = s3_path
            else:
                validation_result["s3_path"] = None

            normalized = normalizer.normalize(parsed)

            print(f"Normalized Data: {normalized}")

            crossValidator = CrossValidationService(
                applicant_dao=applicant_dao, address_dao=address_dao
            )
            crossValidation_result = await crossValidator.validate_drivers_license(
                application_id, normalized
            )

            if not crossValidation_result.valid:
                validation_result["cross_validation_mismatches"] = [
                    m.__dict__ for m in crossValidation_result.mismatches
                ]
                validation_result["valid"] = (
                    crossValidation_result.valid and validation_result["valid"]
                )

            # Add metadata from Dynamsoft
            validation_result["barcode_confidence"] = item.get_confidence()
            print(f"Validation Result: {validation_result}")
            return validation_result

    return {"error": "No  barcode found in image.", "valid": False}


# # --- 3. EXECUTION ---
# if __name__ == "__main__":
#     test_image = r"C:\Users\Ajaykumar.Bhukya\Documents\Learning_LangGraph\ocr\USA_fixed.jpg"  # noqa: E501

#     if os.path.exists(test_image):
#         final_output = process_single_dl(test_image)
#         import json
#         print(json.dumps(final_output, indent=4))
#     else:
#         print("File not found.")
