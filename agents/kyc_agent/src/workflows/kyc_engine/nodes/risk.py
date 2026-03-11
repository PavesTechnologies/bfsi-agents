"""
Risk Aggregation Engine – Policy-Driven, Auditable Decision Core
Aligned with KYC Domain Spec (Decision Matrix, Hard Stops, Audit Artifacts)
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.workflows.kyc_engine.kyc_state import KYCState
from src.workflows.kyc_engine.rules.executor import execute_rules
from src.workflows.kyc_engine.rules.loader import load_rule_set
from src.utils.audit_decorator import audit_node
from src.repositories.kyc_repo.kyc_repository import KYCRepository
from src.core.database import get_db
import asyncio


@track_node("risk_aggregation_engine")
@audit_node(agent_name="kyc_agent")
def risk_aggregator_node(state: KYCState) -> KYCState:
    # ==================================================
    # 1️⃣ Load Rule Set (Versioned Policy)
    # ==================================================
    rule_set = load_rule_set("kyc_rules.yaml")

    rule_version = rule_set["metadata"]["version"]
    # rule_file_hash = rule_set.get("_file_hash")

    thresholds = rule_set.get("thresholds", {})
    weights = rule_set.get("weights", {})

    # ==================================================
    # 2️⃣ Extract Signals
    # ==================================================
    ssn = state.get("ssn_validation") or {}
    address = state.get("address_verification") or {}
    # document = state.get("document_check") or {}
    # face = state.get("face_check") or {}
    aml = state.get("aml_check") or {}

    signals = {
        "ssn": ssn,
        "address": address,
        # "document": document,
        # "face": face,
        "aml": aml,
    }

    # ==================================================
    # 3️⃣ Execute Rule Engine
    # ==================================================
    rule_result = execute_rules(rule_set=rule_set, signals=signals)

    final_status = rule_result["final_status"]
    triggered_rules: list[str] = rule_result.get("triggered_rules", [])
    soft_flags: list[str] = rule_result.get("soft_flags", [])

    # Separate hard-fail rules (if FAIL)
    hard_fail_rules = []
    if final_status == "FAIL":
        hard_fail_rules = triggered_rules.copy()

    hard_fail_triggered = final_status == "FAIL"

    # ==================================================
    # 4️⃣ Weighted Confidence Score (0.0–1.0)
    # ==================================================
    confidence_score = (
        ssn.get("ssn_score", 1.0) * weights.get("ssn", 0.25)
        + (1 - address.get("risk_score", 0.0)) * weights.get("address", 0.34)
        +
        # document.get("document_score", 1.0) * weights.get("document", 0.25) +
        # face.get("face_match_score", 1.0) * weights.get("face", 0.25) +
        (1 - aml.get("aml_score", 0.0)) * weights.get("aml", 0.25)
    )

    confidence_score = round(confidence_score, 4)

    # ==================================================
    # 5️⃣ Decision Snapshot (Audit Safe)
    # ==================================================
    decision_snapshot: dict = {
        "rule_version": rule_version,
        "thresholds": thresholds,
        "signals": signals,
        "triggered_rules": triggered_rules,
        "final_status": final_status,
        "confidence_score": confidence_score,
    }

    reasoning_trace = {
        "decision_snapshot": decision_snapshot,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # ==================================================
    # 6️⃣ Build Final RiskDecisionState
    # ==================================================
    risk_decision = {
        "final_status": final_status,
        "confidence_score": confidence_score,
        "hard_fail_triggered": hard_fail_triggered,
        "decision_reason": "Rule-based evaluation completed",
        "triggered_rules": triggered_rules,
        "soft_flags": soft_flags,
        "hard_fail_rules": hard_fail_rules,
        "rule_version": rule_version,
        "decision_rules_snapshot": {
            "hard_fail_triggered": hard_fail_triggered,
            "soft_signal_count": len(soft_flags),
        },
        "model_versions": {"aggregator_engine": "v2.0", "rule_version": rule_version},
        "reasoning_trace": reasoning_trace,
    }

    risk_decision_data = {"risk_decision": risk_decision}

    # Persistence logic for Storable Returns
    async def persist():
        try:
            async for session in get_db():
                repo = KYCRepository(session)
                # Note: kyc_id is needed. State should have it or applicant_id to find latest.
                kyc_id = state.get("kyc_id")
                if not kyc_id:
                    # Alternative: find latest by applicant_id if kyc_id not in state
                    applicant_id = state.get("applicant_id")
                    if applicant_id:
                        latest = await repo.get_latest_attempt(applicant_id)
                        if latest:
                            kyc_id = latest.id
                
                if kyc_id:
                    await repo.save_risk_decision(kyc_id, risk_decision_data["risk_decision"])
                break
        except Exception as e:
            print(f"Error persisting KYC risk decision: {e}")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(persist())
        else:
            asyncio.run(persist())
    except Exception as e:
        print(f"Loop management error: {e}")

    return risk_decision_data
