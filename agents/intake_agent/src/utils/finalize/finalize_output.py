from datetime import datetime
from typing import Dict, Any, List
from pydantic import ValidationError
from src.domain.output.los_schema import LOSOutput


# ---------------- CANONICAL BUILDER ----------------
def build_canonical(application: dict, applicants: list, enrichments: dict, evidence: list):
    return {
        "application": application or {},
        "applicants": applicants or [],
        "enrichments": enrichments or {},
        "evidence": sorted(evidence, key=lambda x: x.get("path", "")),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


# ---------------- SCHEMA VALIDATION ----------------
class LOSValidationError(Exception):
    pass


def validate_schema(output: dict):
    try:
        LOSOutput(**output)
    except ValidationError as e:
        raise LOSValidationError(str(e))


# ---------------- ORM → DICT MAPPER ----------------
def map_application(loan):
    return {
        "application_id": str(loan.application_id),
        "loan_type": loan.loan_type,
        "loan_purpose": loan.loan_purpose,
        "requested_amount": loan.requested_amount,
        "requested_term_months": loan.requested_term_months,
        "preferred_payment_day": loan.preferred_payment_day,
        "origination_channel": loan.origination_channel,
        "application_status": str(loan.application_status),
    }


def map_applicants(loan):
    out = []
    for a in loan.applicant:
        primary_address = None
        if a.address:
            addr = a.address[0]
            primary_address = {
                "line1": addr.address_line1 or "",
                "line2": addr.address_line2 or "",
                "city": addr.city or "",
                "state": addr.state or "",
                "pincode": addr.zip_code or "",
            }

        out.append({
            "applicant_id": str(a.applicant_id),
            "applicant_role": a.applicant_role or "primary",
            "first_name": a.first_name,
            "middle_name": a.middle_name,
            "last_name": a.last_name,
            "email": a.email,
            "phone_number": a.phone_number,
            "date_of_birth": a.date_of_birth.isoformat() if a.date_of_birth else None,
            "aadhaar_number": a.aadhaar_encrypted,
            "pan_number": a.pan_number,
            "address": primary_address,
        })
    return out
