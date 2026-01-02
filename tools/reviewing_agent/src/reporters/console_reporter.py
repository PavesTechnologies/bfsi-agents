from typing import List
import json
from domain.rules.base import Finding
from adapters.github_adapter import to_repo_relative


def print_report(findings: List[Finding]) -> None:
    if not findings:
        print("✅ Reviewing Agent: no issues found")
        return

    print("\n🔍 Reviewing Agent Findings\n")

    for f in findings:
        location = f.file or "N/A"
        line = f.line or "-"
        print(
            f"[{f.severity}] {f.rule_id} | {location}:{line}\n"
            f"  → {f.message}"
        )
        if f.suggestion:
            print(f"  💡 Suggestion: {f.suggestion}")
        print()

    print(
        f"Summary: {len(findings)} finding(s) "
        f"({sum(1 for f in findings if f.severity == 'ERROR')} errors, "
        f"{sum(1 for f in findings if f.severity == 'WARNING')} warnings)"
    )

def print_summary(findings, llm_insights):
    print("\n=== Reviewing Agent Summary ===\n")

    for f in findings:
        print(f"[{f.severity}] {f.rule_id}: {f.message}")
        if f.file:
            print(f"  File: {to_repo_relative(f.file)}")
        if f.suggestion:
            print(f"  Suggestion: {f.suggestion}")
        print()

    if llm_insights:
        print("\n--- LLM Insights ---\n")
        for i in llm_insights:
            print(f"File : {i['file']}")
            print(json.dumps(i, indent=2))
            print()

