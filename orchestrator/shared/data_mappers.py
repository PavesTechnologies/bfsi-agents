"""
Inter-Agent Data Mappers

Functions that transform one agent's output into the next agent's input.
These follow the payload transformation mappings defined in the architecture plan.
"""

from typing import Dict, Any, List, Optional


# ─────────────────────────────────────────────────────────────
# 1. Intake → KYC Mapper
# ─────────────────────────────────────────────────────────────

def map_intake_to_kyc(
    application_id: str,
    applicant: Dict[str, Any],
    idempotency_key: str,
) -> Dict[str, Any]:
    """
    Transform an Intake Agent applicant record into a KYC Agent trigger payload.

    Args:
        application_id: UUID from the Intake Agent's LoanIntakeResponse.
        applicant: The primary applicant dict (from ApplicantSchema).
        idempotency_key: Unique key for idempotent KYC invocation.

    Returns:
        A dict matching KYCTriggerRequest shape.
    """
    # Build full name
    parts = [
        applicant.get("first_name", ""),
        applicant.get("middle_name", ""),
        applicant.get("last_name", ""),
    ]
    full_name = " ".join(p for p in parts if p).strip()

    # Find current address
    addresses = applicant.get("addresses", [])
    current_address = next(
        (a for a in addresses if a.get("address_type") == "current"),
        addresses[0] if addresses else {},
    )

    return {
        "applicant_id": application_id,
        "full_name": full_name,
        "dob": applicant.get("date_of_birth"),
        "ssn": applicant.get("ssn", ""),
        "address": {
            "line1": current_address.get("address_line1", ""),
            "line2": current_address.get("address_line2"),
            "city": current_address.get("city", ""),
            "state": current_address.get("state", ""),
            "zip": current_address.get("zip_code", ""),
        },
        "phone": applicant.get("phone_number", ""),
        "email": applicant.get("email", ""),
        "idempotency_key": idempotency_key,
    }


# ─────────────────────────────────────────────────────────────
# 2. KYC + Intake → Decisioning Mapper
# ─────────────────────────────────────────────────────────────

def map_to_underwriting(
    application_id: str,
    raw_experian_data: Dict[str, Any],
    requested_amount: float,
    requested_tenure_months: int,
    incomes: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Transform KYC-cleared applicant data + Experian credit report into
    the Decisioning Agent's UnderwritingRequest shape.

    Args:
        application_id: UUID from the Intake Agent.
        raw_experian_data: Full Experian JSON credit report.
        requested_amount: Loan amount from the intake application.
        requested_tenure_months: Loan tenure from the intake application.
        incomes: List of income records from the Intake Agent's IncomeSchema.

    Returns:
        A dict matching UnderwritingRequest shape.
    """
    monthly_income = 0.0
    if incomes:
        monthly_income = sum(
            inc.get("monthly_amount", 0.0) for inc in incomes
        )

    return {
        "application_id": application_id,
        "raw_experian_data": raw_experian_data,
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
