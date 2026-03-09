"""
Final Response Composer
LOS-Compatible Structured Output Builder
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node
from src.repositories.underwriting_repository import UnderwritingRepository
from src.core.database import get_db
import asyncio


@track_node("final_response_engine")
@audit_node(agent_name="decisioning_agent")
def final_response_node(state: LoanApplicationState) -> LoanApplicationState:

    final_decision = state.get("final_decision", {})
    counter_offer = state.get("counter_offer_data")
    decision_type = final_decision.get("decision", "UNKNOWN")

    # ==================================================
    # Build the structured response payload
    # ==================================================
    response_payload = {
        "application_id": state.get("application_id"),
        "decision": decision_type,
        "risk_tier": state.get("aggregated_risk_tier"),
        "risk_score": state.get("aggregated_risk_score"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if decision_type == "APPROVE":
        response_payload["loan_details"] = {
            "approved_amount": final_decision.get("approved_amount"),
            "approved_tenure_months": final_decision.get("approved_tenure"),
            "interest_rate": final_decision.get("interest_rate"),
            "disbursement_amount": final_decision.get("disbursement_amount"),
            "explanation": final_decision.get("explanation"),
        }

    elif decision_type == "COUNTER_OFFER":
        response_payload["counter_offer"] = counter_offer
        response_payload["original_decision_explanation"] = final_decision.get("explanation")

    elif decision_type == "DECLINE":
        response_payload["decline_reason"] = final_decision.get("explanation")
        response_payload["reasoning_steps"] = final_decision.get("reasoning_steps", [])

    response_data = {"final_response_payload": response_payload}

    # Persistence logic for Storable Returns
    async def persist():
        try:
            async for session in get_db():
                repo = UnderwritingRepository(session)
                await repo.save_decision(response_data["final_response_payload"])
                break
        except Exception as e:
            print(f"Error persisting underwriting decision: {e}")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(persist())
        else:
            asyncio.run(persist())
    except Exception as e:
        print(f"Loop management error: {e}")

    return response_data