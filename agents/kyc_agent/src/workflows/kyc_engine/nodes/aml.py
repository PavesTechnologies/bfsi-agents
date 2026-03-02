"""
AML / OFAC Screening Node

Uses the existing Experian mock adapter output (FraudShield, RiskModel,
PublicRecord) to derive AML / sanctions signals.
"""

from src.adapters.mock_adapters.mock_experian_adapter import MockExperianAdapter
from src.core.telemetry import track_node
from src.workflows.kyc_engine.kyc_state import AMLCheckState, KYCState


@track_node("aml")
async def aml_node(state: KYCState) -> KYCState:
    req = state["raw_request"]

    adapter = MockExperianAdapter()

    experian_data = adapter.get_credit_report(
        {
            "firstName": req["full_name"].split()[0],
            "lastName": req["full_name"].split()[-1],
            "street1": req["address"]["line1"],
            "city": req["address"]["city"],
            "state": req["address"]["state"],
            "zip": req["address"]["zip"],
            "ssn": req["ssn"],
            "dob": str(req["dob"]),
        }
    )

    # -------------------------------------------------
    # Extract Signals From Experian Response
    # -------------------------------------------------
    experian_data = await experian_data
    fraud_shield = experian_data.fraudShield[0]
    fraud_code = fraud_shield.fraudShieldIndicators.indicator[0]

    credit_score = float(experian_data.riskModel[0].score)
    public_records = experian_data.publicRecord
    has_public_record = len(public_records) > 0

    deceased_flag = bool(fraud_shield.dateOfDeath)

    flags: dict[str, str] = {}

    # -------------------------------------------------
    # Fraud Code Mapping
    # -------------------------------------------------
    # 00 → clean
    # 01 → bankruptcy / low score
    # 08 → synthetic
    # 09 → deceased
    # 12 → known fraud hit (OFAC-like)

    ofac_match = fraud_code == "12"
    pep_match = fraud_code in {"01", "08", "09"}

    if fraud_code != "00":
        flags["EXPERIAN_FRAUD_CODE"] = fraud_code

    if has_public_record:
        flags["PUBLIC_RECORD_PRESENT"] = "True"

    if deceased_flag:
        flags["DECEASED_SSN_FLAG"] = "True"

    # -------------------------------------------------
    # AML Risk Score Calculation (0.0 – 1.0)
    # -------------------------------------------------

    # Baseline risk derived from credit score
    base_risk = 1.0 - (credit_score / 1000.0)

    # Fraud penalty
    if fraud_code != "00":
        base_risk += 0.20

    # Public record penalty
    if has_public_record:
        base_risk += 0.10

    # Deceased penalty
    if deceased_flag:
        base_risk += 0.20

    # OFAC hard bump
    if ofac_match:
        base_risk = 1.0

    aml_score = round(max(0.0, min(1.0, base_risk)), 4)

    aml_state: AMLCheckState = {
        "ofac_match": ofac_match,
        "ofac_confidence": 0.99 if ofac_match else 0.30,
        "pep_match": pep_match,
        "sanctions_list_version": "EXPERIAN-MOCK-2026-01",
        "aml_score": aml_score,
        "flags": flags,
    }

    return {
        "aml_check": aml_state,
    }
