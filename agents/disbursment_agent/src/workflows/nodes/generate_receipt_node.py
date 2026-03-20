"""
Node 4: Generate Disbursement Receipt

Compiles all disbursement data into a final structured receipt
that can be returned via the API or stored in a database.
"""

from src.services.receipt_builder import build_receipt
from src.workflows.state import DisbursementState
from src.utils.audit_decorator import audit_node


@audit_node(agent_name="disbursement_agent")
def generate_receipt_node(state: DisbursementState) -> dict:
    """
    Builds the final DisbursementReceipt from the accumulated state.
    Includes a schedule preview (first 3 + last installment).
    """

    return {"disbursement_receipt": build_receipt(state)}
