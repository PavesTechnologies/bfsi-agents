"""
Final Response Composer
LOS-Compatible Structured Output Builder
"""

from datetime import datetime
from typing import Any

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node


def _build_rag_summary(state: LoanApplicationState) -> dict[str, Any] | None:
    """
    Surface what the rag_retrieval_node fetched and what each analyzer
    consumed. Returns None when no retrieval ran (existing /underwrite
    and /underwrite/cibil flows skip this node, so their payloads stay
    untouched).
    """
    pool = state.get("rag_pool") or []
    contexts = state.get("rag_context_per_node") or {}

    if not pool and not contexts:
        return None

    sources = sorted({(chunk.get("source_collection") or "") for chunk in pool})
    documents = sorted({(chunk.get("source_document") or "") for chunk in pool if chunk.get("source_document")})

    pool_preview = []
    for chunk in pool:
        pool_preview.append({
            "id": chunk.get("id"),
            "source_collection": chunk.get("source_collection"),
            "source_document": chunk.get("source_document"),
            "section_number": chunk.get("section_number"),
            "section_title": chunk.get("section_title"),
            "breadcrumb": chunk.get("breadcrumb"),
            "page_numbers": chunk.get("page_numbers"),
            "score": chunk.get("score"),
        })

    return {
        "pool_size": len(pool),
        "collections": [s for s in sources if s],
        "source_documents": documents,
        "per_node_context": contexts,
        "pool": pool_preview,
    }


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
        "correlation_id": state.get("correlation_id"),
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
        response_payload["max_approved_amount"] = final_decision.get("max_approved_amount")

    elif decision_type == "DECLINE":
        response_payload["decline_reason"] = final_decision.get("explanation")
        response_payload["reasoning_steps"] = final_decision.get("reasoning_steps", [])

    # Attach RAG summary only for the Indian variant (rag_retrieval_node ran).
    # Existing flows leave this empty, so their payload shape is unchanged.
    rag_summary = _build_rag_summary(state)
    if rag_summary is not None:
        response_payload["rag_response"] = rag_summary

    return {"final_response_payload": response_payload}
