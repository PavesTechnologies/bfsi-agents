"""
Indian variant of the underwriting graph.

Shape is identical to decision_flow.build_underwriting_graph(), with two
extra serial nodes between `pi_deletion` and the parallel fan-out:
  * `rag_retrieval` — fetches RBI guidelines (regulatory backdrop, shared by
                      all analyzers).
  * `rules_loader`  — reads bank_rules from the bank-admin DB and stages
                      structured + formatted rule context per analyzer node.

Bank-policy thresholds are NOT loaded from RAG anymore — banks tune them via
bank-admin-service's HITL approval workflow and the next application picks
up the new values immediately.

Checkpoint lifecycle: the AsyncConnectionPool is opened per-request via
`indian_workflow_session()` and closed when the graph finishes. We do NOT
keep a long-lived pool; idle Postgres connections get terminated by the
server after ~5 min and used to cause stale-connection failures on the next
request.
"""

from contextlib import asynccontextmanager

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
from src.workflows.decision_engine.nodes.rules_loader_node import rules_loader_node
from src.workflows.decision_engine.nodes.utilization_node import utilization_node
from src.workflows.decision_state import LoanApplicationState

settings = get_settings()
DB_URI = settings.DATABASE_GENERIC


def _build_indian_graph_builder() -> StateGraph:
    """Return the uncompiled StateGraph for the Indian underwriting flow.
    Cheap — no DB. The checkpointer is attached per-request inside
    `indian_workflow_session()`."""

    graph = StateGraph(LoanApplicationState)

    # --- Nodes -----------------------------------------------------
    graph.add_node("pi_deletion", pi_deletion_node)
    graph.add_node("rag_retrieval", rag_retrieval_node)
    graph.add_node("rules_loader", rules_loader_node)

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

    # --- pi_deletion -> rag_retrieval -> rules_loader (serial) -----
    graph.add_edge("pi_deletion", "rag_retrieval")
    graph.add_edge("rag_retrieval", "rules_loader")

    # --- rules_loader -> 7 parallel analyzers ----------------------
    graph.add_edge("rules_loader", "credit_score")
    graph.add_edge("rules_loader", "public_record")
    graph.add_edge("rules_loader", "credit_utilization")
    graph.add_edge("rules_loader", "debt_exposure")
    graph.add_edge("rules_loader", "payment_behavior")
    graph.add_edge("rules_loader", "inquiry")
    graph.add_edge("rules_loader", "income_analysis")

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

    return graph


@asynccontextmanager
async def indian_workflow_session():
    """Per-request lifecycle for the Indian/RAG-augmented underwriting graph.

    Opens an `AsyncConnectionPool` + `AsyncPostgresSaver` checkpointer for the
    duration of one graph invocation, compiles the graph against it, yields
    the runnable workflow, then closes the pool on exit.

    Usage:
        async with indian_workflow_session() as workflow:
            final_state = await workflow.ainvoke(initial_state, config=config)
    """
    async with AsyncConnectionPool(conninfo=DB_URI, min_size=1, max_size=2) as pool:
        await pool.wait()
        checkpointer = AsyncPostgresSaver(pool)
        workflow = _build_indian_graph_builder().compile(checkpointer=checkpointer)
        yield workflow
