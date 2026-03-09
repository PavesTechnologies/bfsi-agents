"""
Node 3: Execute Fund Transfer

Calls the (mocked) banking gateway to simulate the
actual disbursement of funds to the borrower's account.
"""

from src.workflows.state import DisbursementState
from src.services.banking_gateway import execute_fund_transfer, BankingGatewayError
from src.utils.audit_decorator import audit_node


@audit_node(agent_name="disbursement_agent")
def execute_transfer_node(state: DisbursementState) -> dict:
    """
    Triggers a fund transfer via the banking gateway.
    On success, updates state with transaction_id and timestamp.
    On failure, marks the disbursement as FAILED.
    """

    application_id = state.get("application_id", "UNKNOWN")
    disbursement_amount = state.get("disbursement_amount", 0)

    try:
        result = execute_fund_transfer(
            application_id=application_id,
            disbursement_amount=disbursement_amount,
        )

        return {
            "disbursement_status": "DISBURSED",
            "transaction_id": result["transaction_id"],
            "transfer_timestamp": result["timestamp"],
        }

    except BankingGatewayError as e:
        return {
            "disbursement_status": "FAILED",
            "error": f"Fund transfer failed: {str(e)}",
        }
