"""
Workflow State (LangGraph Only)
"""

from typing import TypedDict
from agents.intake_agent.src.domain.agent_context import AgentContext


class WorkflowState(TypedDict):
    context: AgentContext
    retries: int
