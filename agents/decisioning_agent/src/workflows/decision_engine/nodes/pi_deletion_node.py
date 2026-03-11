"""
PI Deletion Engine
Sanitizes Personally Identifiable Information (PII)
from Experian payload before downstream underwriting.
"""

from datetime import datetime
from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node
import copy

@track_node("pi_deletion_engine")
@audit_node(agent_name="decisioning_agent")
def pi_deletion_node(state: LoanApplicationState) -> LoanApplicationState:

    # ==================================================
    # 1️⃣ Extract Raw Bureau Payload
    # ==================================================
    raw_experian_data = state.get("raw_experian_data", {})
    
    # Create a copy so we work on the data directly without mutating the original state
    sanitized_payload = copy.deepcopy(raw_experian_data) if raw_experian_data else {}

    # ==================================================
    # 2️⃣ Remove PII Keys Directly
    # ==================================================
    
    # 1. Consumer Identity (Names)
    for name in sanitized_payload.get("consumerIdentity", {}).get("name", []):
        name.pop("firstName", None)
        name.pop("middleName", None)
        name.pop("surname", None)

    # 2. Address Information
    for addr in sanitized_payload.get("addressInformation", []):
        for key in ["streetPrefix", "streetName", "streetSuffix", "unitType", "unitId", "city", "state", "zipCode"]:
            addr.pop(key, None)

    # 3. Employment Information
    for emp in sanitized_payload.get("employmentInformation", []):
        emp.pop("name", None)

    # 4. Tradelines (Financial Accounts)
    for trade in sanitized_payload.get("tradeline", []):
        trade.pop("accountNumber", None)

    # 5. Public Records
    for record in sanitized_payload.get("publicRecord", []):
        record.pop("courtName", None)
        record.pop("referenceNumber", None)

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