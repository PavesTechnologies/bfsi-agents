from .review_state import ReviewState


def initial_review_state() -> ReviewState:
    return {
        "changed_files": [],
        "findings": [],
        "signals": [],
        "llm_insights": [],
    }
