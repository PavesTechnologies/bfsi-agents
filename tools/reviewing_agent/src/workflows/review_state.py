from typing import TypedDict, List, Any


class ReviewState(TypedDict):
    changed_files: List[Any]
    findings: List[Any]
    signals: List[Any]
    llm_insights: List[Any]
