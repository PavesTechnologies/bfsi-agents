#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path
from typing import List

from rules.base import Finding
from rules.naming_rules import check_agent_folder_names
from rules.structure_rules import (
    check_agent_structure,
    check_gitkeep_for_empty_dirs,
)
from rules.import_rules import check_import_boundaries
from rules.size_rules import check_file_size, check_function_size


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = REPO_ROOT / "agents"


# -----------------------------
# Git helpers
# -----------------------------

def get_changed_files() -> List[Path]:
    """
    Returns a list of changed files compared to the base branch.
    Works for both PRs and direct pushes.
    """
    base_ref = os.getenv("GITHUB_BASE_REF")

    if base_ref:
        diff_cmd = ["git", "diff", "--name-only", f"origin/{base_ref}"]
    else:
        diff_cmd = ["git", "diff", "--name-only", "HEAD~1"]

    try:
        result = subprocess.run(
            diff_cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return []

    files = []
    for line in result.stdout.splitlines():
        path = REPO_ROOT / line.strip()
        if path.exists():
            files.append(path)

    return files


def is_agent_file(path: Path) -> bool:
    return "agents" in path.parts and path.suffix == ".py"


def get_agent_root(path: Path) -> Path | None:
    """
    agents/<agent_name>/...
    """
    try:
        idx = path.parts.index("agents")
        return Path(*path.parts[: idx + 2])
    except ValueError:
        return None


# -----------------------------
# Rule execution
# -----------------------------

def run_rules(changed_files: List[Path]) -> List[Finding]:
    findings: List[Finding] = []

    # Repo-level rules
    findings.extend(check_agent_folder_names(REPO_ROOT))

    # Group files by agent
    agents = set()
    for f in changed_files:
        agent = get_agent_root(f)
        if agent:
            agents.add(agent)

    for agent_path in agents:
        findings.extend(check_agent_structure(agent_path))
        findings.extend(check_gitkeep_for_empty_dirs(agent_path))

    # File-level rules
    for file_path in changed_files:
        if not is_agent_file(file_path):
            continue

        findings.extend(check_import_boundaries(file_path))
        findings.extend(check_file_size(file_path))
        findings.extend(check_function_size(file_path))

    return findings


# -----------------------------
# Reporting
# -----------------------------

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


# -----------------------------
# Entry point
# -----------------------------

def main():
    print("🚦 Reviewing Agent started")

    changed_files = get_changed_files()
    if not changed_files:
        print("ℹ️ No changed files detected")
        return

    findings = run_rules(changed_files)
    print_report(findings)

    print("🚦 Reviewing Agent finished (non-blocking)")


if __name__ == "__main__":
    main()
