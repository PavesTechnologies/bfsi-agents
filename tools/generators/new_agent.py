#!/usr/bin/env python3

"""
Usage:
    python tools/generators/new_agent.py <agent_name>

Example:
    python tools/generators/new_agent.py kyc_agent
"""

from string import Template
import sys
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = ROOT / "agents"
TEMPLATES_DIR = Path(__file__).parent / "templates"


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
    "src/__init__.py",
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

[[tool.poetry.packages]]
include = "src"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.110.0"
uvicorn = "^0.29.0"
langgraph = "^0.0.40"
pydantic = "^2.6.0"

[tool.poetry.scripts]
dev = "src.cli:dev"
prod = "src.cli:prod"
test = "src.cli:test"

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
        return True
    except FileNotFoundError:
        print("Poetry not found. Skipping poetry install.")
        return False
    except subprocess.CalledProcessError:
        print("poetry install failed. Fix manually.")
        return False

def populate_templates_recursively(agent_base: Path, context: dict):
    """
    Recursively walk templates/ and materialize them
    into the new agent directory.

    - Preserves folder structure
    - Renders templates using str.format
    - Never overwrites existing non-empty files
    """

    for template_path in TEMPLATES_DIR.rglob("*.tpl"):
        relative_path = template_path.relative_to(TEMPLATES_DIR)

        # Remove .tpl suffix
        target_relative_path = relative_path.with_suffix("")

        target_path = agent_base / target_relative_path

        if target_path.exists() and target_path.stat().st_size > 0:
            continue  # never overwrite user code

        template = Template(template_path.read_text())
        rendered = template.safe_substitute(**context)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(rendered.strip() + "\n")


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
    populate_templates_recursively(agent_path / "src", {"agent_name": agent_name})
    write_poetry_config(agent_path, agent_name)
    # write_boilerplate(agent_path, agent_name)

    print(f"Agent structure created at agents/{agent_name}")

    # Optional: run poetry install
    poetry_install_success = run_poetry_install(agent_path)

    print("Agent setup complete.")
    if poetry_install_success:
        print(f"Get started by running: \n cd agents/{agent_name} \n poetry run dev")


if __name__ == "__main__":
    main()
