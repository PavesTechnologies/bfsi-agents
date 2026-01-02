from pathlib import Path
from typing import List

from core.config import REPO_ROOT
from domain.rules.base import Finding
from domain.rules.import_rules import check_import_boundaries
from domain.rules.naming_rules import check_agent_folder_names
from domain.rules.size_rules import check_file_size, check_function_size
from domain.rules.structure_rules import check_agent_structure, check_gitkeep_for_empty_dirs

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

