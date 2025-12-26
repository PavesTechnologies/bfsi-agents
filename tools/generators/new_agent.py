#!/usr/bin/env python3

"""
Usage:
    python tools/generators/new_agent.py <agent_name>

Example:
    python tools/generators/new_agent.py kyc_agent
"""

import sys
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = ROOT / "agents"

# Directories that usually start empty → need .gitkeep
EMPTY_DIRS = [
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

FILES_TO_CREATE = [
    "src/app.py",
    "src/main.py",
    "README.md",
    "pyproject.toml",
]


def validate_agent_name(name: str) -> str:
    if not re.match(r"^[a-z][a-z0-9_]*_agent$", name):
        print(
            "Invalid agent name.\n"
            "Use snake_case and end with '_agent'.\n"
            "Example: intake_agent, kyc_agent"
        )
        sys.exit(1)
    return name


def create_dirs_with_gitkeep(base: Path):
    for rel_path in EMPTY_DIRS:
        dir_path = base / rel_path
        dir_path.mkdir(parents=True, exist_ok=True)
        gitkeep = dir_path / ".gitkeep"
        gitkeep.touch(exist_ok=True)


def create_files(base: Path):
    for rel_path in FILES_TO_CREATE:
        file_path = base / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch(exist_ok=True)


def write_poetry_config(base: Path, agent_name: str):
    pyproject = base / "pyproject.toml"
    if pyproject.stat().st_size != 0:
        return

    pyproject.write_text(
        f"""
[tool.poetry]
name = "{agent_name.replace('_', '-')}"
version = "0.1.0"
description = "{agent_name} microservice"
authors = ["Agentic Platform Team"]
package-mode = false

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.110.0"
uvicorn = "^0.29.0"
langgraph = "^0.0.40"
pydantic = "^2.6.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
ruff = "^0.3.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""".strip()
    )


def write_boilerplate(base: Path, agent_name: str):
    app_py = base / "src/app.py"
    main_py = base / "src/main.py"
    readme = base / "README.md"

    if app_py.stat().st_size == 0:
        app_py.write_text(
            f"""from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="{agent_name}")
    return app
"""
        )

    if main_py.stat().st_size == 0:
        main_py.write_text(
            """from src.app import create_app

app = create_app()
"""
        )

    if readme.stat().st_size == 0:
        readme.write_text(
            f"""# {agent_name}

Agent microservice for {agent_name.replace("_agent", "").replace("_", " ").title()}.

## Responsibilities
- Single agent responsibility
- Standard agent folder structure
- LangGraph-based workflow orchestration

## Notes
See repo-level docs for architecture and coding rules.
"""
        )


def run_poetry_install(agent_path: Path):
    try:
        subprocess.run(
            ["poetry", "install"],
            cwd=agent_path,
            check=True,
        )
        print("poetry install completed")
    except FileNotFoundError:
        print("Poetry not found. Skipping poetry install.")
    except subprocess.CalledProcessError:
        print("poetry install failed. Fix manually.")


def main():
    if len(sys.argv) != 2:
        print("Usage: python new_agent.py <agent_name>")
        sys.exit(1)

    agent_name = validate_agent_name(sys.argv[1])
    agent_path = AGENTS_DIR / agent_name

    if agent_path.exists():
        print(f"Agent '{agent_name}' already exists.")
        sys.exit(1)

    print(f"Creating new agent: {agent_name}")

    create_dirs_with_gitkeep(agent_path)
    create_files(agent_path)
    write_poetry_config(agent_path, agent_name)
    write_boilerplate(agent_path, agent_name)

    print(f"Agent structure created at agents/{agent_name}")

    # Optional: run poetry install
    run_poetry_install(agent_path)

    print("Agent setup complete.")


if __name__ == "__main__":
    main()
