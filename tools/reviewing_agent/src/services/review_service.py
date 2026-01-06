from services.llm.parser import parse_llm_output
from collections import defaultdict
from pathlib import Path
from typing import List

from adapters.llm_adapter import ask_llm
from domain.signals.models import Signal
from services.llm.prompts import TYPE2_PROMPT, TYPE2_XML_PROMPT
from services.signal_engine import select_primary_signal, should_trigger_llm
from services.layer_policy import LAYER_POLICIES, violates_layer_policy
from core.config import REPO_ROOT

def detect_layer(path: str) -> str:
    if "/src/domain/" in path:
        return "domain"
    if "/src/services/" in path:
        return "services"
    if "/src/workflows/" in path:
        return "workflows"
    return "unknown"

import subprocess

def to_repo_relative(path: str | None) -> str | None:
    if not path:
        return None

    try:
        path = str(Path(path).resolve().relative_to(REPO_ROOT))
        path = path.replace("\\", "/")  
        return path
    except Exception:
        return path


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
        primary_signal = select_primary_signal(file_signals)

        contexts.append(
            {
                "file": to_repo_relative(file),
                "layer": layer,
                "signals": file_signals,
                "diff": diff,
                "architecture_contract": ARCHITECTURE_CONTRACT,
                "primary_line": primary_signal.line if primary_signal else None,
                "primary_signal": primary_signal.type if primary_signal else None,
            }
        )

    return contexts


def review_with_llm(contexts: List[dict]) -> List[dict]:
    insights = []

    for ctx in contexts:
        layer = ctx["layer"]

        policy = LAYER_POLICIES[layer]
        
        # prompt = TYPE2_PROMPT.format(
        #     architecture_contract=ctx["architecture_contract"],
        #     file=ctx["file"],
        #     layer=layer,
        #     signals=ctx["signals"].__str__(),
        #     primary_signal=ctx["primary_signal"],
        #     diff=ctx["diff"][:3000],
        #     allow_local_fixes=str(policy['allow_local_fixes']),
        #     allowed_actions="\n  ".join(policy['allowed_actions']),
        #     forbidden_suggestions="\n  ".join(policy['forbidden_suggestions']),
        # )

        prompt = TYPE2_XML_PROMPT.format(
        file=ctx["file"],
        layer=layer,
        primary_signal=ctx["primary_signal"],
        signals=str(ctx["signals"]),
        diff=ctx["diff"][:3000],
        allow_local_fixes=str(policy["allow_local_fixes"]),
        allowed_actions="\n".join(
            f"      <ACTION>{a}</ACTION>" for a in policy["allowed_actions"]
        ),
        forbidden_suggestions="\n".join(
            f"      <SUGGESTION>{s}</SUGGESTION>" for s in policy["forbidden_suggestions"]
        ),
    )




        # print(f"-----------------------------\nLLM Prompt for {ctx['file']}:\n{prompt}\n---\n")

        raw = ask_llm(prompt)

        # print(f"LLM Response for {ctx['file']}:\n{raw}\n---\n")

        parsed = parse_llm_output(raw)
        if not parsed:
            print(f"Failed to parse LLM output for {ctx['file']}:\n{raw}")
            continue  # discard junk / NONE / malformed

        
        if violates_layer_policy(parsed, layer):
            print(f"Disallowed suggestion detected for layer {layer}: {parsed['action']}")
            continue

        insights.append(
            {
                "file": ctx["file"],
                "issue": parsed["issue"],
                "action": parsed["action"],
                "line": ctx["primary_line"],

            }
        )

    return insights

def run_llm_review(signals):
    if should_trigger_llm(signals):
        llm_context = build_llm_context(signals)
        llm_insights = review_with_llm(llm_context)
        return llm_insights
    return []
