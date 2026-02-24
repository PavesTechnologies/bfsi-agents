# src/workflows/decision_flow.py
"""
KYC Agent - Parallel Execution Graph
"""

from langgraph.graph import END, StateGraph

from src.workflows.kyc_engine.kyc_state import KYCState
from src.workflows.kyc_engine.nodes.address import address_node
from src.workflows.kyc_engine.nodes.aml import aml_node

# --- Import Nodes ---
from src.workflows.kyc_engine.nodes.contact import contact_node
from src.workflows.kyc_engine.nodes.explanation import explanation_node
from src.workflows.kyc_engine.nodes.face import face_node
from src.workflows.kyc_engine.nodes.human_review import human_review_node
from src.workflows.kyc_engine.nodes.normalize import normalize_node
from src.workflows.kyc_engine.nodes.risk import risk_aggregator_node
from src.workflows.kyc_engine.nodes.ssn import ssn_node

# from IPython.display import Image, display # type: ignore


def build_graph():
    graph = StateGraph(KYCState)

    # -----------------------
    # Register Nodes
    # -----------------------

    graph.add_node("normalize", normalize_node)

    graph.add_node("ssn", ssn_node)
    graph.add_node("address", address_node)
    graph.add_node("face", face_node)
    graph.add_node("aml", aml_node)
    graph.add_node("contact", contact_node)

    graph.add_node("aggregate", risk_aggregator_node)
    graph.add_node("human_review", human_review_node)
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
    graph.add_edge("normalize", "face")
    graph.add_edge("normalize", "aml")
    graph.add_edge("normalize", "contact")

    # -----------------------
    # Join → Aggregator
    # -----------------------

    graph.add_edge("ssn", "aggregate")
    graph.add_edge("address", "aggregate")
    graph.add_edge("face", "aggregate")
    graph.add_edge("aml", "aggregate")
    graph.add_edge("contact", "aggregate")

    # -----------------------
    # Conditional Routing
    # -----------------------

    def route_after_aggregation(state: KYCState):
        decision = state.get("risk_decision", {}).get("final_status")

        if decision == "NEEDS_HUMAN_REVIEW":
            return "human_review"
        else:
            return "explanation"

    graph.add_conditional_edges(
        "aggregate",
        route_after_aggregation,
        {
            "human_review": "human_review",
            "explanation": "explanation",
        },
    )

    # After human review → explanation
    graph.add_edge("human_review", "explanation")

    # Final node
    graph.add_edge("explanation", END)

    return graph.compile()


# workflow = build_graph()

# result = workflow.invoke({})
# print("Final KYC Result:")
# print(result)
