"""
Decision Interpreter (Domain)

Validates and interprets LLM output into domain truth.
"""

from src.domain.agent_context import Decision


def interpret_decision(raw: dict) -> tuple[Decision, str]:
    decision = raw.get("decision")
    reason = raw.get("reason")

    if decision not in Decision.__members__:
        raise ValueError(f"Invalid decision: {decision}")

    if not reason:
        raise ValueError("Missing decision reason")

    return Decision[decision], reason
