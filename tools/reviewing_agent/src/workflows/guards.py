from .review_state import ReviewState


def should_call_llm(state: ReviewState) -> str:
    """
    Decides whether LLM review should run.
    """
    if state["signals"]:
        return "llm_node"
    return "report_node"
