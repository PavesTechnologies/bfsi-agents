"""
Disbursement Agent - Domain Decision Interpreter

Validates and interprets the decision received from the Decisioning Agent.
"""

from src.domain.agent_context import DecisionType


def interpret_decision(decision_str: str) -> DecisionType:
    """
    Validate that the decision string is a recognized decision type.

    Args:
        decision_str: Raw decision string (e.g., "APPROVE", "COUNTER_OFFER", "DECLINE").

    Returns:
        A DecisionType enum value.

    Raises:
        ValueError: If the decision string is not recognized.
    """
    try:
        return DecisionType(decision_str)
    except ValueError:
        raise ValueError(
            f"Invalid decision type: '{decision_str}'. "
            f"Expected one of: {[d.value for d in DecisionType]}"
        )
