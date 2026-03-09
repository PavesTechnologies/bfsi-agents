"""
Node 4: Generate Disbursement Receipt

Compiles all disbursement data into a final structured receipt
that can be returned via the API or stored in a database.
"""

from src.workflows.state import DisbursementState
from src.utils.audit_decorator import audit_node
from src.repositories.disbursement_repository import DisbursementRepository
from src.core.database import get_db
import asyncio


@audit_node(agent_name="disbursement_agent")
def generate_receipt_node(state: DisbursementState) -> dict:
    """
    Builds the final DisbursementReceipt from the accumulated state.
    Includes a schedule preview (first 3 + last installment).
    """

    schedule = state.get("repayment_schedule", [])

    # Build a compact schedule preview
    schedule_preview = []
    if schedule:
        # First 3 installments
        schedule_preview = schedule[:3]
        # Last installment (if not already included)
        if len(schedule) > 3:
            schedule_preview.append(schedule[-1])

    approved_amount = state.get("approved_amount", 0)
    disbursement_amount = state.get("disbursement_amount", 0)
    origination_fee = round(approved_amount - disbursement_amount, 2)

    receipt = {
        "application_id": state.get("application_id", "UNKNOWN"),
        "disbursement_status": state.get("disbursement_status", "UNKNOWN"),
        "decision_type": state.get("decision", "UNKNOWN"),

        # Amounts
        "approved_amount": approved_amount,
        "disbursement_amount": disbursement_amount,
        "origination_fee_deducted": origination_fee,

        # Loan Terms
        "interest_rate": state.get("interest_rate", 0),
        "tenure_months": state.get("approved_tenure_months", 0),
        "monthly_emi": state.get("monthly_emi", 0),
        "total_interest": state.get("total_interest", 0),
        "total_repayment": state.get("total_repayment", 0),
        "first_emi_date": state.get("first_emi_date", ""),

        # Transfer Details
        "transaction_id": state.get("transaction_id"),
        "transfer_timestamp": state.get("transfer_timestamp"),

        # Schedule Preview
        "schedule_preview": schedule_preview,

        # Explanation
        "explanation": state.get("explanation"),
    }

    receipt_payload = {
        "disbursement_receipt": receipt,
    }

    # Persistence logic for Storable Returns
    async def persist():
        async for session in get_db():
            repo = DisbursementRepository(session)
            await repo.save_record(receipt_payload["disbursement_receipt"])
            break

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(persist())
        else:
            asyncio.run(persist())
    except Exception as e:
        print(f"Error persisting disbursement record: {e}")

    return receipt_payload
