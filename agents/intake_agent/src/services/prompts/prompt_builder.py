"""
Prompt Builder (Service)

Assembles final prompt with runtime data.
"""

from agents.intake_agent.src.domain.prompts.decision_prompt import DECISION_PROMPT
from agents.intake_agent.src.domain.agent_context import AgentContext


def build_prompt(context: AgentContext) -> str:
    return f"""
{DECISION_PROMPT}

Input:
{context["input_text"]}
""".strip()
