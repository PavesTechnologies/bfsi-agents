from utils.source import find_next_code_line
from pathlib import Path
from domain.signals.aggregator import collect_signals
from domain.signals.models import SIGNAL_PRIORITY, Signal
from core.config import REPO_ROOT


def is_llm_eligible(path: str) -> bool:    
    print(f"Checking LLM eligibility for path: {path}")
    if not "/agents/" in path:
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
        and ( "LARGE_FUNCTION" in types 
        or "HIGH_COMPLEXITY" in types )
    )


def select_primary_signal(signals: list[Signal]) -> Signal | None:
    if not signals:
        return None

    primary = min(
        signals,
        key=lambda s: (
            SIGNAL_PRIORITY.get(s.type, 99),
            s.line if s.line is not None else 10**9,
        ),
    )

    if primary.line is not None:
        normalized = find_next_code_line(primary.file, primary.line)
        if normalized is not None:
            primary.line = normalized

    return primary
