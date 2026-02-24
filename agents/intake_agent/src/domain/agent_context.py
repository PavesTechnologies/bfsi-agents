"""
Agent Business Context (Domain)

Represents business facts and decisions.
Independent of LangGraph and LLM vendors.
"""

from enum import StrEnum
from typing import TypedDict
from uuid import UUID


class Decision(StrEnum):
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
    reason: str | None
    # Metadata fields (required, flattened for simplicity)
    ip_address: str
    user_agent: str | None
    browser: str | None
    os: str | None
    device_type: str | None
    accept_language: str | None
    referrer: str | None
