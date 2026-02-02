"""
Agent Business Context (Domain)

Represents business facts and decisions.
Independent of LangGraph and LLM vendors.
"""

from typing import TypedDict, Optional
from enum import Enum
from uuid import UUID


class Decision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AgentContext(TypedDict, total=False):
    """Main context for agent processing.

    Metadata is REQUIRED for all requests (no Optional).
    Downstream always receives metadata.
    """
    request_id: UUID
    app_id: UUID
    input_text: str
    decision: Decision
    reason: Optional[str]
    # Metadata fields (required, flattened for simplicity)
    ip_address: str
    user_agent: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    device_type: Optional[str]
    accept_language: Optional[str]
    referrer: Optional[str]
