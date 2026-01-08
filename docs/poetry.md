# Poetry Guide

## What Is Poetry?

Poetry is a **Python dependency and packaging tool**.

In practical terms, Poetry helps you:

* Define project dependencies in one place
* Create isolated virtual environments automatically
* Install exactly the same dependencies across machines
* Run project commands in a predictable environment

Instead of manually managing virtual environments and `requirements.txt` files, Poetry handles this in a single, structured workflow.

---

## Why We Use Poetry

We use Poetry to ensure:

* Everyone runs the project with the same dependency versions
* Local development matches CI and production more closely
* Adding or upgrading dependencies is explicit and traceable
* Onboarding new developers is faster and more reliable

These benefits become more important as the codebase and team grow.

---

## Core Concepts

### Virtual Environments

Poetry automatically creates and manages a **virtual environment** for each project.

This means:

* Project dependencies do not leak into your global Python installation
* Different projects can safely use different dependency versions

You usually do **not** need to create or activate virtual environments manually when using Poetry.

---

### pyproject.toml

The `pyproject.toml` file is the **single source of truth** for the project.

It defines:

* Project metadata (name, version, description)
* Python version compatibility
* Project dependencies
* Development-only dependencies
* Tooling configuration (formatters, linters, test tools)

Think of `pyproject.toml` as a combination of:

* `requirements.txt`
* `setup.py`
* Tool configuration files

all in one place.

---

## Understanding pyproject.toml (High Level)

A typical `pyproject.toml` contains several sections:

### `[tool.poetry]`

Defines basic project information:

* Project name
* Version
* Description
* Authors

This section is mostly informational but is required for packaging.

---

### `[tool.poetry.dependencies]`

Lists **runtime dependencies** required for the application to run.

Example:

```toml
[tool.poetry.dependencies]
python = ">=3.10,<3.13"
fastapi = "^0.110"
```

Key points:

* Versions are explicit
* Python version is defined here
* These dependencies are installed in all environments

---

### `[tool.poetry.group.dev.dependencies]`

Lists **development-only dependencies**.

Typical examples:

* linters
* formatters
* test frameworks

These are not required in production but are essential for local development.

---

### `[build-system]`

Defines how the project is built.

In most cases, this section should not be modified unless you know exactly why.

---

## poetry.lock

The `poetry.lock` file records the **exact versions** of all installed dependencies (including transitive ones).

Important points:

* This file ensures reproducible installs
* It should be committed to version control
* It is updated automatically by Poetry

When dependencies differ between machines, this file is usually the reason.

---

## Common Poetry Commands

### Install Dependencies

```bash
poetry install
```

Installs all dependencies defined in `pyproject.toml` using `poetry.lock`.

This is typically the first command to run after cloning the repository.

---

### Add a Dependency

```bash
poetry add requests
```

Adds a runtime dependency and updates both `pyproject.toml` and `poetry.lock`.

For development-only dependencies:

```bash
poetry add --group dev pytest
```

---

### Remove a Dependency

```bash
poetry remove requests
```

Removes the dependency cleanly from the project.

---

### Run Commands Inside the Environment

```bash
poetry run pytest
poetry run python src/main.py
```

This ensures commands run with the correct dependencies.

---

### Activate the Virtual Environment

```bash
poetry shell
```

Spawns a shell inside the project’s virtual environment.

This is optional—`poetry run` is often sufficient.

---

### Check Environment Info

```bash
poetry env info
```

Shows details about the active virtual environment.

---

## Typical Workflow

1. Clone the repository
2. Run `poetry install`
3. Use `poetry run ...` to execute commands
4. Add or update dependencies via `poetry add`

This workflow keeps environments consistent and predictable.

---

## Common Pitfalls

* Editing `poetry.lock` manually
* Installing dependencies with `pip` instead of Poetry
* Ignoring Python version constraints in `pyproject.toml`

Avoiding these helps prevent subtle environment issues.

---

## Summary

Poetry provides a structured, reliable way to manage Python projects.

By standardizing dependency management and environments, it reduces setup friction today and makes long-term maintenance and refactoring easier as the project grows.

Use Poetry consistently, and it will quietly remove an entire class of problems from day-to-day devel
