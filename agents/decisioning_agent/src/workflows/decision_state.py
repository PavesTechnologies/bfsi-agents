"""
Workflow State (LangGraph Only)
"""

from typing import TypedDict


class DecisionState(TypedDict):
    payload: dict
    retries: int
