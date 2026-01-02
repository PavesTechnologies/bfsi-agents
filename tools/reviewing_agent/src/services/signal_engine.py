from pathlib import Path
from domain.signals.aggregator import collect_signals
from domain.signals.models import Signal


def is_llm_eligible(file_path: str) -> bool:
    path = file_path.replace("\\", "/")

    if not path.startswith("agents/"):
        return False

    return any(p in path for p in [
        "/src/domain/",
        "/src/services/",
        "/src/workflows/",
    ])


def filter_llm_eligible_signals(signals: list[Signal]) -> list[Signal]:
    return [s for s in signals if is_llm_eligible(s.file)]


def should_trigger_llm(signals: list[Signal]) -> bool:
    types = {s.type for s in signals}

    return (
        "SENSITIVE_LAYER" in types
        and ("LARGE_FUNCTION" in types or "HIGH_COMPLEXITY" in types)
    )
