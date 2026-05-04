"""
Inter-Agent Data Mappers

Functions that transform one agent's output into the next agent's input.
These follow the payload transformation mappings defined in the architecture plan.
"""

from typing import Dict, Any, List, Optional


# ─────────────────────────────────────────────────────────────
# 1. Intake → India KYC Mapper
# ─────────────────────────────────────────────────────────────

def map_intake_to_india_kyc(
    application_id: str,
    applicant: Dict[str, Any],
    idempotency_key: str,
) -> Dict[str, Any]:
    """
    Transform an Intake Agent applicant record into the India KYC Agent
    trigger payload for POST /india/kyc/execute.

    Args:
        application_id: UUID string from the Intake Agent.
        applicant: Primary applicant dict from raw_application["applicants"][0].
        idempotency_key: Unique key passed as X-Idempotency-Key header (not in body).

    Returns:
        A dict matching KYCRequest shape expected by the India KYC endpoint.
    """
    name_parts = filter(None, [
        applicant.get("first_name", ""),
        applicant.get("middle_name"),
        applicant.get("last_name", ""),
    ])
    full_name = " ".join(name_parts).strip()

    addresses = applicant.get("addresses", [])
    primary_address = next(
        (a for a in addresses if a.get("address_type") in ("current", "permanent")),
        addresses[0] if addresses else {},
    )

    return {
        "application_id": application_id,
        "applicant_data": {
            "applicant_id": applicant.get("applicant_id", application_id),
            "full_name": full_name,
            "dob": str(applicant.get("date_of_birth", "")),
            "aadhaar_number": applicant.get("aadhaar_no") or applicant.get("aadhaar_number", ""),
            "pan_number": applicant.get("pan_number", ""),
            "phone": applicant.get("phone_number", ""),
            "email": applicant.get("email", ""),
            "address": {
                "line1": primary_address.get("address_line1", ""),
                "line2": primary_address.get("address_line2", ""),
                "city": primary_address.get("city", ""),
                "state": primary_address.get("state", ""),
                "pincode": primary_address.get("zip_code", ""),
            },
        },
    }


# ─────────────────────────────────────────────────────────────
# 2. Intake → CIBIL Underwriting Mapper (post-KYC)
# ─────────────────────────────────────────────────────────────

def map_intake_to_cibil_underwriting(
    application_id: str,
    applicant: Dict[str, Any],
    requested_amount: float,
    requested_tenure_months: int,
) -> Dict[str, Any]:
    """
    Transform Intake Agent applicant data into the Decisioning Agent's
    CIBILUnderwritingRequest payload for POST /underwrite/cibil.

    KYC has already verified the applicant's identity at this point.
    The PAN number is used by the decisioning agent to fetch the CIBIL
    report — it is not passed from the KYC response but taken directly
    from intake data.

    Args:
        application_id: UUID string from the Intake Agent.
        applicant: Primary applicant dict from raw_application["applicants"][0].
        requested_amount: Loan amount in INR from raw_application.
        requested_tenure_months: Loan tenure from raw_application.

    Returns:
        A dict matching CIBILUnderwritingRequest shape.
    """
    name_parts = filter(None, [
        applicant.get("first_name", ""),
        applicant.get("middle_name"),
        applicant.get("last_name", ""),
    ])
    full_name = " ".join(name_parts).strip()

    incomes = applicant.get("incomes", [])
    monthly_income = sum(
        float(inc.get("monthly_amount", 0.0)) for inc in incomes
    )

    return {
        "application_id": application_id,
        "pan": applicant.get("pan_number", ""),
        "full_name": full_name,
        "requested_amount": requested_amount,
        "requested_tenure_months": requested_tenure_months,
        "monthly_income": monthly_income,
    }


# ─────────────────────────────────────────────────────────────
# 3. Decisioning → Disbursement Mapper
# ─────────────────────────────────────────────────────────────

def map_decisioning_to_disbursement(
    decisioning_response: Dict[str, Any],
    selected_option_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Transform the Decisioning Agent's resolved response into the
    Disbursement Agent's DisbursementRequest shape.

    By the time this is called, the pipeline_service has already resolved
    the correct loan terms into decisioning_response (flat fields), so
    this is a straight field projection regardless of APPROVE or COUNTER_OFFER.

    Args:
        decisioning_response: uw_data with flat approved_amount, interest_rate, etc.
        selected_option_id: Unused — option resolution happens upstream in pipeline_service.

    Returns:
        A dict matching DisbursementRequest shape.
    """
    return {
        "application_id": decisioning_response.get("application_id"),
        "approved_amount": decisioning_response.get("approved_amount"),
        "approved_tenure_months": decisioning_response.get("approved_tenure_months"),
        "interest_rate": decisioning_response.get("interest_rate"),
        "disbursement_amount": decisioning_response.get("disbursement_amount"),
        "explanation": decisioning_response.get("explanation")
            or decisioning_response.get("terms_summary"),
    }
