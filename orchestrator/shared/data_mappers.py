"""
Inter-Agent Data Mappers

Functions that transform one agent's output into the next agent's input.
These follow the payload transformation mappings defined in the architecture plan.
"""

from typing import Dict, Any, Optional, List


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
    Transform the Decisioning Agent's final response into the
    Disbursement Agent's DisbursementRequest shape.

    Args:
        decisioning_response: The final_response_payload from the Decisioning Agent.
        selected_option_id: If decision is COUNTER_OFFER and user accepted an option.

    Returns:
        A dict matching DisbursementRequest shape.
    """
    decision = decisioning_response.get("decision", "DECLINE")

    payload = {
        "application_id": decisioning_response.get("application_id"),
        "decision": decision,
        "risk_tier": decisioning_response.get("risk_tier"),
        "risk_score": decisioning_response.get("risk_score"),
    }

    if decision == "APPROVE":
        payload["loan_details"] = decisioning_response.get("loan_details")

    elif decision == "COUNTER_OFFER":
        payload["counter_offer"] = decisioning_response.get("counter_offer")
        payload["selected_option_id"] = selected_option_id

    elif decision == "DECLINE":
        payload["decline_reason"] = decisioning_response.get("decline_reason")

    return payload
