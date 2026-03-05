"""
Disbursement Workflow

LangGraph-based execution pipeline for loan disbursement.

Architecture:
  validate_decision → [route] → generate_schedule → execute_transfer → generate_receipt → END
                     ↘ (if invalid) → generate_receipt → END
"""

from langgraph.graph import StateGraph, END
from src.workflows.state import DisbursementState

from src.workflows.nodes.validate_decision_node import validate_decision_node
from src.workflows.nodes.generate_schedule_node import generate_schedule_node
from src.workflows.nodes.execute_transfer_node import execute_transfer_node
from src.workflows.nodes.generate_receipt_node import generate_receipt_node


def build_disbursement_graph():
    """Build and compile the disbursement LangGraph."""

    graph = StateGraph(DisbursementState)

    # ─── Register Nodes ───
    graph.add_node("validate_decision", validate_decision_node)
    graph.add_node("generate_schedule", generate_schedule_node)
    graph.add_node("execute_transfer", execute_transfer_node)
    graph.add_node("generate_receipt", generate_receipt_node)

    # ─── Entry Point ───
    graph.set_entry_point("validate_decision")

    # ─── Conditional Routing after Validation ───
    def route_after_validation(state: DisbursementState):
        """
        If validation passed → proceed to schedule generation.
        If validation failed → skip straight to receipt (with error/rejection info).
        """
        if state.get("validation_passed"):
            return "generate_schedule"
        else:
            return "generate_receipt"

    graph.add_conditional_edges(
        "validate_decision",
        route_after_validation,
        {
            "generate_schedule": "generate_schedule",
            "generate_receipt": "generate_receipt",
        },
    )

    # ─── Linear Edges: Schedule → Transfer → Receipt ───
    graph.add_edge("generate_schedule", "execute_transfer")
    graph.add_edge("execute_transfer", "generate_receipt")

    # ─── Terminal ───
    graph.add_edge("generate_receipt", END)

    return graph.compile()
