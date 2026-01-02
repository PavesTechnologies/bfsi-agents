

import subprocess
from pathlib import Path
from typing import List
import os

from core.config import REPO_ROOT


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
