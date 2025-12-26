import re
from pathlib import Path
from .base import Finding

AGENT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*_agent$")

def check_agent_folder_names(repo_root: Path) -> list[Finding]:
    findings = []
    agents_dir = repo_root / "agents"

    if not agents_dir.exists():
        return findings

    for agent in agents_dir.iterdir():
        if not agent.is_dir():
            continue

        if not AGENT_NAME_PATTERN.match(agent.name):
            findings.append(
                Finding(
                    rule_id="R1.1",
                    severity="ERROR",
                    message=f"Invalid agent folder name: {agent.name}",
                    file=str(agent),
                    suggestion="Agent folders must be snake_case and end with '_agent'"
                )
            )

    return findings
