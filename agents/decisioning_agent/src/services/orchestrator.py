"""
Workflow Orchestrator
"""

from src.workflows.decision_flow import build_graph

_graph = build_graph()


def run_agent(input_text: str) -> dict:
    final_state = _graph.invoke(
        {
            "context": {"input_text": input_text},
            "retries": 0,
        }
    )
    return final_state["context"]
