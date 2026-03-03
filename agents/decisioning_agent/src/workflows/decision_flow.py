"""
Decision Workflow

Determines execution path.
"""

from langgraph.graph import END, StateGraph
from src.services.decision_llm_service import run_decision
from src.workflows.decision_state import DecisionState

# -------------------------------------------
# |   Nodes(if increase move to nodes.py)   |
# -------------------------------------------


def execute_decision(state: DecisionState) -> DecisionState:
    return {
        **state,
        "context": run_decision(state["context"]),
    }


# -------------------------------
# |   Workflow execution path   |
# -------------------------------


def build_graph():
    graph = StateGraph(DecisionState)

    graph.add_node("decide", execute_decision)
    graph.set_entry_point("decide")
    graph.add_edge("decide", END)

    return graph.compile()
