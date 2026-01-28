"""
Decision LLM Service

Executes the full LLM interaction:
- build prompt
- call LLM
- parse response
- interpret business meaning
"""

from src.domain.agent_context import AgentContext
from src.domain.decision_interpreter import interpret_decision
from src.services.prompts.prompt_builder import build_prompt
from src.services.llm_response_parser import parse_llm_response
from src.adapters.llm.openai_adapter import call_llm


def run_decision(context: AgentContext) -> AgentContext:
    prompt = build_prompt(context)
    raw_text = call_llm(prompt)
    parsed = parse_llm_response(raw_text)

    decision, reason = interpret_decision(parsed)

    return {
        **context,
        "decision": decision,
        "reason": reason,
    }
