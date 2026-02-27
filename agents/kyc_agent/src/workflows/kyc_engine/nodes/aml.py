"""
AML / OFAC Screening Node

Uses the existing Experian mock adapter output (FraudShield, RiskModel,
PublicRecord) to derive AML / sanctions signals.
"""

from src.adapters.mock_adapters.mock_experian_adapter import MockExperianAdapter
from src.core.telemetry import track_node
from src.workflows.kyc_engine.kyc_state import AMLCheckState, KYCState


@track_node("aml")
def aml_node(state: KYCState) -> KYCState:
    req = state["raw_request"]

    # Re-use the Experian mock adapter with the same style of payload
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

    # ---- Derive AML signals from Experian mock response ----
    fraud_shield = experian_data.fraudShield[0]
    fraud_code = fraud_shield.fraudShieldIndicators.indicator[0]
    score_raw = float(experian_data.riskModel[0].score)
    has_public_record = len(experian_data.publicRecord) > 0

    flags: dict[str, str] = {}

    # Map Experian fraud codes into AML semantics
    # 00 → clean, 01 → low score / bankruptcy, 08 → synthetic,
    # 09 → deceased, 12 → known fraud hit (treat as OFAC-like).
    ofac_match = fraud_code == "12"
    pep_match = fraud_code in {"01", "08", "09"}

    if fraud_code != "00":
        flags["EXPERIAN_FRAUD_CODE"] = fraud_code

    if has_public_record:
        # In the mock, publicRecord is used for bankruptcy scenarios.
        flags["PUBLIC_RECORD_PRESENT"] = "True"

    # Convert credit score to a 0–1 AML risk score (higher = more risk).
    # Baseline from credit score, then bump for fraud / public record.
    base_risk = max(0.0, min(1.0, 1.0 - score_raw / 1000.0))
    if fraud_code != "00":
        base_risk = min(1.0, base_risk + 0.2)
    if has_public_record:
        base_risk = min(1.0, base_risk + 0.1)

    aml_state: AMLCheckState = {
        "ofac_match": ofac_match,
        "ofac_confidence": 0.95 if ofac_match else 0.3,
        "pep_match": pep_match,
        "sanctions_list_version": "EXPERIAN-MOCK-2026-01",
        "aml_score": round(base_risk, 4),
        "flags": flags,
    }

    return {
        "aml_check": aml_state,
    }
