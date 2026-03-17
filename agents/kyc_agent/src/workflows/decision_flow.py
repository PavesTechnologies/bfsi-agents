# src/workflows/decision_flow.py
"""
KYC Agent - Parallel Execution Graph
"""

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool 

from src.workflows.kyc_engine.kyc_state import KYCState
from src.workflows.kyc_engine.nodes.address import address_node
from src.workflows.kyc_engine.nodes.aml import aml_node

# --- Import Nodes ---
from src.workflows.kyc_engine.nodes.contact import contact_node
from src.workflows.kyc_engine.nodes.explanation import explanation_node
from src.workflows.kyc_engine.nodes.normalize import normalize_node
from src.workflows.kyc_engine.nodes.risk import risk_aggregator_node
from src.workflows.kyc_engine.nodes.ssn import ssn_node
from src.core.config import get_settings

settings = get_settings()

# from IPython.display import Image, display # type: ignore
DB_URI = settings.DATABASE_GENERIC
# ✅ Create pool and checkpointer as module-level singletons (not yet open)
connection_pool = AsyncConnectionPool(conninfo=DB_URI, max_size=10, open=False)
checkpointer = AsyncPostgresSaver(connection_pool)

def build_graph():
    graph = StateGraph(KYCState)

    # -----------------------
    # Register Nodes
    # -----------------------

    graph.add_node("normalize", normalize_node)

    graph.add_node("ssn", ssn_node)
    graph.add_node("address", address_node)
    # graph.add_node("face", face_node)
    graph.add_node("aml", aml_node)
    graph.add_node("contact", contact_node)

    graph.add_node("aggregate", risk_aggregator_node)
    # graph.add_node("human_review", human_review_node)
    graph.add_node("explanation", explanation_node)

    # -----------------------
    # Entry Point
    # -----------------------

    graph.set_entry_point("normalize")

    # -----------------------
    # Parallel Fan-Out
    # -----------------------

    graph.add_edge("normalize", "ssn")
    graph.add_edge("normalize", "address")
    # graph.add_edge("normalize", "face")
    graph.add_edge("normalize", "aml")
    graph.add_edge("normalize", "contact")

    # -----------------------
    # Join → Aggregator
    # -----------------------

    graph.add_edge("ssn", "aggregate")
    graph.add_edge("address", "aggregate")
    # graph.add_edge("face", "aggregate")
    graph.add_edge("aml", "aggregate")
    graph.add_edge("contact", "aggregate")

    # -----------------------
    # Conditional Routing
    # -----------------------

    # def route_after_aggregation(state: KYCState):
    #     decision = state.get("risk_decision", {}).get("final_status")

    #     if decision == "NEEDS_HUMAN_REVIEW":
    #         return "human_review"
    #     else:
    #         return "explanation"

    # graph.add_conditional_edges(
    #     "aggregate",
    #     route_after_aggregation,
    #     {
    #         "human_review": "human_review",
    #         "explanation": "explanation",
    #     },
    # )

    # After human review → explanation
    graph.add_edge("aggregate", "explanation")

    # Final node
    graph.add_edge("explanation", END)

    # workflow = graph.compile()

    # with open("graph.png", "wb") as f:
    #     f.write(workflow.get_graph().draw_mermaid_png())

    # Ideally, the checkpointer is created outside or managed via a pool
    # DB_URI = "postgresql://avnadmin:AVNS_X0ml0E8DUSxuuhGnQZX@pg-22ef5b8a-ajaykumar.h.aivencloud.com:15549/kyc_agent"
    # connection_pool = AsyncConnectionPool(conninfo=DB_URI, max_size=10,open=False)
    # checkpointer = AsyncPostgresSaver(connection_pool)
    
    workflow = graph.compile(checkpointer=checkpointer)
    
    # 2. Attach the pool and checkpointer to the workflow object 
    # so we can open them from the Service or FastAPI startup
    workflow.pool = connection_pool
    workflow.checkpointer = checkpointer
    
    return workflow


# workflow = build_graph()

# result = workflow.invoke({})
# print("Final KYC Result:")
# print(result)
