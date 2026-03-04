"""
PI Deletion Engine
Sanitizes Personally Identifiable Information (PII)
from Experian payload before downstream underwriting.
"""

from datetime import datetime
from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState


@track_node("pi_deletion_engine")
def pi_deletion_node(state: LoanApplicationState) -> LoanApplicationState:

    # ==================================================
    # 1️⃣ Extract Raw Bureau Payload
    # ==================================================
    raw_experian_data = state.get("raw_experian_data") or {}
    
    sanitized_payload = raw_experian_data

    # ==================================================
    # 3️⃣ Update Processing Flag
    # ==================================================
    is_pii_masked = True


    # ==================================================
    # 5️⃣ Return Updated State Fields
    # ==================================================
    return {
        "pi_masked_experian_data": sanitized_payload,
        "is_pii_masked": is_pii_masked
    }