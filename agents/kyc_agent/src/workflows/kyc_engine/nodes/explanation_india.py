from src.core.telemetry import track_node
from src.utils.audit_decorator import audit_node
from src.workflows.kyc_engine.india_kyc_state import IndianKYCState


@track_node("explanation_india")
@audit_node(agent_name="kyc_agent")
def explanation_india_node(state: IndianKYCState) -> IndianKYCState:
    decision = state.get("risk_decision") or {}
    status = decision.get("final_status", "UNKNOWN")
    ckyc_id = (state.get("ckyc") or {}).get("ckyc_id")

    if status == "PASS":
        ckyc_suffix = f" CKYC ID: {ckyc_id}." if ckyc_id else ""
        explanation = f"KYC Decision: PASS – All Indian KYC checks completed successfully.{ckyc_suffix}"

    elif status == "FAIL":
        rules = decision.get("hard_fail_rules", [])
        explanation = f"KYC Decision: FAIL – Hard fail triggered. Rules: {', '.join(rules)}."

    elif status == "NEEDS_HUMAN_REVIEW":
        soft = decision.get("soft_flags", [])
        explanation = f"KYC Decision: NEEDS_HUMAN_REVIEW – Soft flags raised: {', '.join(soft)}."

    else:
        explanation = "KYC Decision: UNKNOWN – Workflow did not complete normally."

    return {"decision_explanation": explanation}
