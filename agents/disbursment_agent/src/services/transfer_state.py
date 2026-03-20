def build_transfer_result(result: dict) -> dict:
    transfer_status = result.get("status", "UNKNOWN")
    disbursement_status = (
        "DISBURSED" if transfer_status == "SUCCESS" else "TRANSFER_PENDING"
    )

    return {
        "disbursement_status": disbursement_status,
        "transaction_id": result["transaction_id"],
        "transfer_status": transfer_status,
        "transfer_timestamp": result["timestamp"],
        "reconciliation_required": transfer_status != "SUCCESS",
        "gateway_response": result,
    }


def build_transfer_failure(error_message: str) -> dict:
    return {
        "disbursement_status": "FAILED",
        "transfer_status": "FAILED",
        "reconciliation_required": False,
        "error": error_message,
    }
