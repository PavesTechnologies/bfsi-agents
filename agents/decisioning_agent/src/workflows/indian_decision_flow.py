"""
Indian variant of the underwriting graph.

Shape is identical to decision_flow.build_underwriting_graph(), with one
extra node — `rag_retrieval` — inserted between `pi_deletion` and the
parallel fan-out. That node fetches RBI / bank policy chunks once,
re-ranks them per analyzer concern, and stashes the result in state so
each analyzer can read its slice without doing its own retrieval.
"""

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from psycopg_pool import AsyncConnectionPool

from src.core.config import get_settings
from src.workflows.decision_engine.nodes.behavior_node import behavior_node
from src.workflows.decision_engine.nodes.counter_offer_node import counter_offer_node
from src.workflows.decision_engine.nodes.credit_score_node import credit_score_node
from src.workflows.decision_engine.nodes.decision_llm_node import decision_llm_node
from src.workflows.decision_engine.nodes.exposure_node import exposure_node
from src.workflows.decision_engine.nodes.final_response_node import final_response_node
from src.workflows.decision_engine.nodes.income_node import income_node
from src.workflows.decision_engine.nodes.inquiry_node import inquiry_node
from src.workflows.decision_engine.nodes.pi_deletion_node import pi_deletion_node
from src.workflows.decision_engine.nodes.public_record_node import public_record_node
from src.workflows.decision_engine.nodes.rag_retrieval_node import rag_retrieval_node
from src.workflows.decision_engine.nodes.risk_aggregator_node import risk_aggregator_node
from src.workflows.decision_engine.nodes.utilization_node import utilization_node
from src.workflows.decision_state import LoanApplicationState

settings = get_settings()
DB_URI = settings.DATABASE_GENERIC

# Module-level pool / checkpointer — opened by the service on first use,
# matching the pattern in decision_flow.py.
indian_connection_pool = AsyncConnectionPool(
    conninfo=DB_URI, min_size=1, max_size=2, open=False,
)
indian_checkpointer = AsyncPostgresSaver(indian_connection_pool)


def build_indian_underwriting_graph():
    graph = StateGraph(LoanApplicationState)

    # --- Nodes -----------------------------------------------------
    graph.add_node("pi_deletion", pi_deletion_node)
    graph.add_node("rag_retrieval", rag_retrieval_node)

    graph.add_node("credit_score", credit_score_node)
    graph.add_node("public_record", public_record_node)
    graph.add_node("credit_utilization", utilization_node)
    graph.add_node("debt_exposure", exposure_node)
    graph.add_node("payment_behavior", behavior_node)
    graph.add_node("inquiry", inquiry_node)
    graph.add_node("income_analysis", income_node)

    graph.add_node("aggregate", risk_aggregator_node)
    graph.add_node("decision", decision_llm_node)
    graph.add_node("counter_offer", counter_offer_node)
    graph.add_node("final_response", final_response_node)

    # --- Entry -----------------------------------------------------
    graph.set_entry_point("pi_deletion")

    # --- pi_deletion -> rag_retrieval (single-threaded) ------------
    graph.add_edge("pi_deletion", "rag_retrieval")

    # --- rag_retrieval -> 7 parallel analyzers ---------------------
    graph.add_edge("rag_retrieval", "credit_score")
    graph.add_edge("rag_retrieval", "public_record")
    graph.add_edge("rag_retrieval", "credit_utilization")
    graph.add_edge("rag_retrieval", "debt_exposure")
    graph.add_edge("rag_retrieval", "payment_behavior")
    graph.add_edge("rag_retrieval", "inquiry")
    graph.add_edge("rag_retrieval", "income_analysis")

    # --- 7 analyzers -> aggregate ---------------------------------
    graph.add_edge("credit_score", "aggregate")
    graph.add_edge("public_record", "aggregate")
    graph.add_edge("credit_utilization", "aggregate")
    graph.add_edge("debt_exposure", "aggregate")
    graph.add_edge("payment_behavior", "aggregate")
    graph.add_edge("inquiry", "aggregate")
    graph.add_edge("income_analysis", "aggregate")

    # --- decision routing -----------------------------------------
    graph.add_edge("aggregate", "decision")

    def route_after_decision(state: LoanApplicationState):
        decision = (state.get("decision_result") or {}).get("decision")
        return "counter_offer" if decision == "COUNTER_OFFER" else "final_response"

    graph.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "counter_offer": "counter_offer",
            "final_response": "final_response",
        },
    )

    graph.add_edge("counter_offer", "final_response")
    graph.add_edge("final_response", END)

    workflow = graph.compile(checkpointer=indian_checkpointer)
    workflow.pool = indian_connection_pool
    workflow.checkpointer = indian_checkpointer
    return workflow
