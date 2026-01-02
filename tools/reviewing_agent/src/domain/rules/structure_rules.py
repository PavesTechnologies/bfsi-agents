from pathlib import Path
from .base import Finding

REQUIRED_FOLDERS = [
    "src/api",
    "src/core",
    "src/domain",
    "src/models",
    "src/services",
    "src/adapters",
    "src/workflows",
    "src/repositories",
    "src/utils",
    "tests",
    "infra",
]

REQUIRED_FILES = [
    "pyproject.toml",
    "src/app.py",
    "src/main.py",
    "README.md",
]

def check_agent_structure(agent_path: Path) -> list[Finding]:
    findings = []

    for folder in REQUIRED_FOLDERS:
        path = agent_path / folder
        if not path.exists():
            findings.append(
                Finding(
                    rule_id="R1.2",
                    severity="ERROR",
                    message=f"Missing required folder: {folder}",
                    file=str(agent_path),
                )
            )

    for file in REQUIRED_FILES:
        path = agent_path / file
        if not path.exists():
            findings.append(
                Finding(
                    rule_id="R1.3",
                    severity="ERROR",
                    message=f"Missing required file: {file}",
                    file=str(agent_path),
                )
            )

    return findings


def check_gitkeep_for_empty_dirs(agent_path: Path) -> list[Finding]:
    findings = []

    for path in agent_path.rglob("*"):
        if path.is_dir():
            files = list(path.iterdir())
            if not files:
                gitkeep = path / ".gitkeep"
                if not gitkeep.exists():
                    findings.append(
                        Finding(
                            rule_id="R1.4",
                            severity="WARNING",
                            message="Empty directory without .gitkeep",
                            file=str(path),
                            suggestion="Add a .gitkeep file to preserve folder structure"
                        )
                    )

    return findings
