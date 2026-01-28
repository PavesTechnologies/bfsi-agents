"""
Workflow State (LangGraph Only)
"""

from typing import TypedDict
from src.domain.agent_context import AgentContext


class WorkflowState(TypedDict):
    context: AgentContext
    retries: int
