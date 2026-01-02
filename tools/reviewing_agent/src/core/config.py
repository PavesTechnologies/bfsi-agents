import os
from pathlib import Path

# Repository root (assumes tools/reviewing_agent/src/core/config.py)
REPO_ROOT = Path(__file__).resolve().parents[4]

AGENTS_DIR = REPO_ROOT / "agents"

LOCAL_DEV = os.getenv("LOCAL_DEV", "false").lower() == "true"
