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
        out.append({
            "applicant_id": str(a.applicant_id),
            "first_name": a.first_name,
            "last_name": a.last_name,
            "email": a.email,
            "phone_number": a.phone_number,
            "date_of_birth": a.date_of_birth.isoformat() if a.date_of_birth else None,
        })
    return out
