# """
# KYC Workflow Orchestrator

# Executes deterministic KYC pipeline:
# Identity → AML → Risk → Decision
# """

# from datetime import datetime

# from src.workflows.kyc_engine.kyc_state import KYCState, KYCStatus
# from src.workflows.kyc_engine.nodes.identity_node import run_identity
# from src.workflows.kyc_engine.nodes.aml_node import run_aml
# from src.workflows.kyc_engine.nodes.risk_node import run_risk, run_decision


# def execute_kyc(state: KYCState) -> KYCState:
#     """Run full KYC workflow deterministically."""

#     # -------------------------
#     # START
#     # -------------------------
#     state.status = KYCStatus.PENDING

#     # -------------------------
#     # IDENTITY
#     # -------------------------
#     state = run_identity(state)
#     if state.hard_fail_triggered:
#         return _finalize_failure(state)

#     # -------------------------
#     # AML
#     # -------------------------
#     state = run_aml(state)
#     if state.hard_fail_triggered:
#         return _finalize_failure(state)

#     # -------------------------
#     # RISK
#     # -------------------------
#     state = run_risk(state)

#     # -------------------------
#     # DECISION
#     # -------------------------
#     state = run_decision(state)

#     return state


# def _finalize_failure(state: KYCState) -> KYCState:
#     """Terminate workflow early due to hard fail."""
#     state.status = KYCStatus.FAILED
#     state.completed_at = datetime.utcnow()
#     return state
