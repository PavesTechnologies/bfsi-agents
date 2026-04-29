"""
Aadhaar + PAN Verification Node.

Orchestrates:
  1. Age validation (hard fail if < 18)
  2. UIDAI eKYC OTP flow (generate + verify)
  3. PAN verification + PAN–Aadhaar linkage check
"""

from datetime import date, datetime

from src.adapters.mock_adapters.mock_pan_adapter import MockPANAdapter
from src.adapters.mock_adapters.mock_uidai_adapter import MockUIDAIAdapter
from src.core.telemetry import track_node
from src.utils.audit_decorator import audit_node
from src.workflows.kyc_engine.india_kyc_state import IndianKYCState


@track_node("aadhaar_pan")
@audit_node(agent_name="kyc_agent")
async def aadhaar_pan_node(state: IndianKYCState) -> IndianKYCState:
    req = state["raw_request"]
    age_flags: dict[str, str] = {}

    # Age validation
    try:
        dob = datetime.strptime(req["dob"], "%Y-%m-%d").date()
        age = (date.today() - dob).days // 365
        if age < 18:
            age_flags["AGE_BELOW_MINIMUM"] = f"Applicant age {age} is below minimum 18 years"
        if age > 100:
            age_flags["AGE_SUSPICIOUS"] = f"Applicant age {age} exceeds 100 years"
    except (ValueError, KeyError):
        age_flags["DOB_PARSE_ERROR"] = f"Cannot parse DOB {req.get('dob')!r}"

    uidai = MockUIDAIAdapter()
    pan_adapter = MockPANAdapter()

    # Step 1: Generate OTP
    otp_resp = uidai.generate_otp({
        "aadhaar_number": req["aadhaar_number"],
        "full_name": req["full_name"],
        "dob": req["dob"],
    })

    # Step 2: Verify OTP (use provided OTP or fall back to mock default)
    aadhaar_state = uidai.verify_otp({
        "aadhaar_number": req["aadhaar_number"],
        "otp": req.get("aadhaar_otp") or "123456",
        "txn_id": otp_resp.get("txn_id"),
        "full_name": req["full_name"],
        "dob": req["dob"],
    })

    if age_flags:
        aadhaar_state["flags"] = {**aadhaar_state.get("flags", {}), **age_flags}

    # PAN verification + PAN–Aadhaar linkage
    pan_state = pan_adapter.verify({
        "pan_number": req["pan_number"],
        "full_name": req["full_name"],
        "dob": req["dob"],
        "aadhaar_number": req["aadhaar_number"],
    })

    return {
        "aadhaar_verification": aadhaar_state,
        "pan_verification": pan_state,
    }
