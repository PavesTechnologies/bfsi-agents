"""
Agent Business Context (Domain)

Represents business facts and decisions.
Independent of LangGraph and LLM vendors.
"""

from enum import StrEnum
from typing import TypedDict


class Decision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AgentContext(TypedDict, total=False):
    input_text: str
    decision: Decision
    reason: str | None
