

import subprocess
from pathlib import Path
from typing import List
import os

from core.config import REPO_ROOT


def get_changed_files() -> List[Path]:
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
            encoding="utf-8",
            check=True,
        )
    except subprocess.CalledProcessError:
        return []

    files = []
    for line in result.stdout.splitlines():
        abs_path = (REPO_ROOT / line.strip()).resolve()
        if abs_path.exists() and abs_path.is_file():
            files.append(abs_path)

    return files


import subprocess
import re

def get_first_changed_line(file_path: str) -> int | None:
    try:
        result = subprocess.run(
            ["git", "diff", "-U0", "--", str(file_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        for line in result.stdout.splitlines():
            # @@ -a,b +c,d @@
            if line.startswith("@@"):
                match = re.search(r"\+(\d+)", line)
                if match:
                    return int(match.group(1))
    except Exception:
        pass

    return None
