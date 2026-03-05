"""
Node 2: Generate Repayment Schedule

Takes the validated loan terms and generates a full
month-by-month amortization schedule using the disbursement calculator.
"""

from src.workflows.state import DisbursementState
from src.services.disbursement_calculator import generate_repayment_schedule


def generate_schedule_node(state: DisbursementState) -> dict:
    """
    Reads approved_amount, interest_rate, and approved_tenure_months
    from the state and generates the repayment schedule.
    """

    principal = state.get("approved_amount", 0)
    annual_rate = state.get("interest_rate", 0)
    tenure_months = state.get("approved_tenure_months", 0)

    schedule = generate_repayment_schedule(
        principal=principal,
        annual_rate=annual_rate,
        tenure_months=tenure_months,
    )

    # Convert installments to list of dicts for JSON serialization
    installments_dicts = [inst.model_dump() for inst in schedule.installments]

    return {
        "disbursement_status": "SCHEDULED",
        "monthly_emi": schedule.monthly_emi,
        "total_interest": schedule.total_interest,
        "total_repayment": schedule.total_repayment,
        "first_emi_date": schedule.first_emi_date,
        "repayment_schedule": installments_dicts,
    }
