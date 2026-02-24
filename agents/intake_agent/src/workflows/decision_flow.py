"""
Decision Workflow

Determines execution path.
"""

from langgraph.graph import END, StateGraph
from src.services.decision_llm_service import run_decision
from src.workflows.state import WorkflowState

# -------------------------------------------
# |   Nodes(if increase move to nodes.py)   |
# -------------------------------------------


def execute_decision(state: WorkflowState) -> WorkflowState:
    return {
        **state,
        "context": run_decision(state["context"]),
    }


# -------------------------------
# |   Workflow execution path   |
# -------------------------------


def build_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node("decide", execute_decision)
    graph.set_entry_point("decide")
    graph.add_edge("decide", END)

    return graph.compile()
