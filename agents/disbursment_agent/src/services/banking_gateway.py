"""
Mock Banking Gateway Service

Simulates an external API call to a Core Banking System (CBS)
or payment gateway to execute a fund transfer.

In production, this would integrate with NEFT/RTGS/IMPS APIs.
"""

import uuid
from datetime import datetime
from typing import Dict, Any


class BankingGatewayError(Exception):
    """Raised when the banking gateway transfer fails."""
    pass


def execute_fund_transfer(
    application_id: str,
    disbursement_amount: float,
    borrower_account: str | None = None,
) -> Dict[str, Any]:
    """
    Simulate sending a fund transfer request to the banking system.

    Args:
        application_id: The loan application ID.
        disbursement_amount: The net amount to transfer.
        borrower_account: Target bank account (mocked).

    Returns:
        A dict with transaction_id, status, and timestamp.

    Raises:
        BankingGatewayError: If the transfer simulation fails.
    """
    # --------------------------------------------------
    # In production, this would be an HTTP call:
    #   POST /api/v1/transfers
    #   {
    #       "reference_id": application_id,
    #       "amount": disbursement_amount,
    #       "beneficiary_account": borrower_account,
    #       "mode": "NEFT"
    #   }
    # --------------------------------------------------

    if disbursement_amount <= 0:
        raise BankingGatewayError(
            f"Invalid disbursement amount: {disbursement_amount}. Must be > 0."
        )

    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gateway_status = "PENDING" if disbursement_amount >= 50000 else "SUCCESS"

    return {
        "transaction_id": transaction_id,
        "status": gateway_status,
        "amount_transferred": disbursement_amount,
        "beneficiary_account": borrower_account or "MOCK-ACCT-XXXX-7890",
        "transfer_mode": "NEFT",
        "timestamp": timestamp,
    }
