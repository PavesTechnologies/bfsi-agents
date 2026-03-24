from src.workflows.state import DisbursementState


def build_receipt(state: DisbursementState) -> dict:
    schedule = state.get("repayment_schedule", [])

    schedule_preview = []
    if schedule:
        schedule_preview = schedule[:3]
        if len(schedule) > 3:
            schedule_preview.append(schedule[-1])

    approved_amount = state.get("approved_amount", 0)
    disbursement_amount = state.get("disbursement_amount", 0)
    origination_fee = round(approved_amount - disbursement_amount, 2)

    return {
        "application_id": state.get("application_id", "UNKNOWN"),
        "disbursement_status": state.get("disbursement_status", "UNKNOWN"),
        "approved_amount": approved_amount,
        "disbursement_amount": disbursement_amount,
        "origination_fee_deducted": origination_fee,
        "interest_rate": state.get("interest_rate", 0),
        "tenure_months": state.get("approved_tenure_months", 0),
        "monthly_emi": state.get("monthly_emi", 0),
        "total_interest": state.get("total_interest", 0),
        "total_repayment": state.get("total_repayment", 0),
        "first_emi_date": state.get("first_emi_date", ""),
        "transaction_id": state.get("transaction_id"),
        "transfer_status": state.get("transfer_status"),
        "transfer_timestamp": state.get("transfer_timestamp"),
        "reconciliation_required": state.get("reconciliation_required", False),
        "schedule_preview": schedule_preview,
        "explanation": state.get("explanation"),
    }
