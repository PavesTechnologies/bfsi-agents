"""
Agent Business Context (Domain)

Represents business facts and decisions.
Independent of LangGraph and LLM vendors.
"""

from typing import TypedDict, Optional
from enum import Enum


class Decision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AgentContext(TypedDict, total=False):
    input_text: str
    decision: Decision
    reason: Optional[str]
