"""
Orchestrator Agent Configuration

Centralized configuration for agent URLs and pipeline settings.
"""

import os


class AgentConfig:
    """Agent endpoint URLs resolved from environment variables with defaults."""

    INTAKE_AGENT_URL: str = os.getenv("INTAKE_AGENT_URL", "http://localhost:8000")
    KYC_AGENT_URL: str = os.getenv("KYC_AGENT_URL", "http://localhost:8001")
    DECISIONING_AGENT_URL: str = os.getenv("DECISIONING_AGENT_URL", "http://localhost:8002")
    DISBURSEMENT_AGENT_URL: str = os.getenv("DISBURSEMENT_AGENT_URL", "http://localhost:8003")

    # Pipeline Settings
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("AGENT_TIMEOUT", "120"))
    # Underwriting needs more time: RAG retrieval + 7 parallel LLMs + decision/counter-offer LLM
    UNDERWRITING_TIMEOUT_SECONDS: int = int(os.getenv("UNDERWRITING_TIMEOUT", "300"))
