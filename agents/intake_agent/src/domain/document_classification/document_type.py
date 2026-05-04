from enum import StrEnum


class DocumentType(StrEnum):
    # India identity documents
    AADHAAR_CARD = "aadhaar_card"
    PAN_CARD = "pan_card"
    VOTER_ID = "voter_id"
    DRIVING_LICENSE_INDIA = "driving_license_india"
    PASSPORT = "passport"

    # India income / financial documents
    BANK_STATEMENT = "bank_statement"
    ITR = "itr"
    FORM_16 = "form_16"
    SALARY_SLIP = "salary_slip"

    # Address / other proofs
    UTILITY_BILL = "utility_bill"
    PHOTO = "photo"
    ADDRESS_PROOF = "address_proof"
    GST_CERTIFICATE = "gst_certificate"
    UDYAM_CERTIFICATE = "udyam_certificate"

    UNKNOWN = "unknown"
