from collections import defaultdict
from pathlib import Path
from typing import List

from adapters.llm_adapter import ask_llm
from domain.signals.models import Signal
from services.llm.prompts import TYPE2_PROMPT
from services.signal_engine import should_trigger_llm

def detect_layer(path: str) -> str:
    if "/src/domain/" in path:
        return "domain"
    if "/src/services/" in path:
        return "services"
    if "/src/workflows/" in path:
        return "workflows"
    return "unknown"

import subprocess


def get_diff_snippet(file_path: str, context_lines: int = 10) -> str:
    """
    Returns a small unified diff snippet for a file.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "diff",
                f"-U{context_lines}",
                "--",
                file_path,
            ],
            capture_output=True,
            check=False,
        )

        if not result.stdout:
            return "" 
        
        return result.stdout.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


def group_signals_by_file(signals: list[Signal]) -> dict[str, list[Signal]]:
    grouped = defaultdict(list)
    for s in signals:
        grouped[s.file].append(s)
    return grouped


ARCHITECTURE_CONTRACT = (
    "Domain logic must be pure and independent of infrastructure. "
    "Services coordinate use cases. "
    "Workflows orchestrate multi-step flows."
)


def build_llm_context(signals: list[Signal]) -> list[dict]:
    """
    Build one LLM context per file.
    """
    contexts = []

    grouped = group_signals_by_file(signals)

    for file, file_signals in grouped.items():
        layer = detect_layer(file)
        diff = get_diff_snippet(file)

        contexts.append(
            {
                "file": file,
                "layer": layer,
                "signals": [s.type for s in file_signals],
                "functions": list(
                    {s.function for s in file_signals if s.function}
                ),
                "diff": diff,
                "architecture_contract": ARCHITECTURE_CONTRACT,
            }
        )

    return contexts


def review_with_llm(contexts: List[dict]) -> List[dict]:
    insights = []

    for ctx in contexts:
        prompt = TYPE2_PROMPT.format(
            architecture_contract=ctx["architecture_contract"],
            file=ctx["file"],
            layer=ctx["layer"],
            signals=", ".join(ctx["signals"]),
            diff=ctx["diff"][:3000],  # hard cap
        )

        response = ask_llm(prompt)

        insights.append(
            {
                "file": ctx["file"],
                "layer": ctx["layer"],
                "signals": ctx["signals"],
                "text": response.strip(),
            }
        )

    return insights

def run_llm_review(signals):
    if should_trigger_llm(signals):
        llm_context = build_llm_context(signals)
        llm_insights = review_with_llm(llm_context)
        return llm_insights
