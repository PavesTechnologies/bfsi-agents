"""Render a per-node rules dict as the same prompt-ready text shape that
`reranker.format_chunks` used to emit for bank_policies RAG hits, so analyzer
prompts see no surprise format change in the {policy_context} slot."""
import json
from typing import Any


_HEADER = "POLICY GUIDANCE (bank rules):"


def format_rules_for_prompt(rules: dict[str, Any]) -> str:
    """`{rule_key: value}` → indented bullet list under a single header.

    JSON-typed values (lists / dicts) are pretty-printed with 2-space indent
    so the LLM can read band tables without us flattening them. Empty dicts
    return an empty string (caller decides whether to inject anything).
    """
    if not rules:
        return ""

    lines: list[str] = [_HEADER]
    for key in sorted(rules.keys()):
        value = rules[key]
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, indent=2, ensure_ascii=False)
            lines.append(f"- {key}:\n{_indent(rendered, 4)}")
        else:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def _indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line for line in text.splitlines())
