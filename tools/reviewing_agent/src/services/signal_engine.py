from pathlib import Path
from domain.signals.aggregator import collect_signals
from domain.signals.models import Signal
from core.config import REPO_ROOT


def is_llm_eligible(file_path: str) -> bool:

    try:
        rel_path = Path(file_path).resolve().relative_to(REPO_ROOT)
    except ValueError:
        return False
    
    path = str(rel_path).replace("\\", "/")

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
        or ("LARGE_FUNCTION" in types or "HIGH_COMPLEXITY" in types)
    )
