# Development Setup

## Purpose

This document explains how to set up the agent service for local development. It is intended to provide a **clear, repeatable path** from cloning the repository to running the service successfully.

Following these steps helps ensure everyone works in a consistent environment, which reduces setup issues and makes debugging and refactoring easier over time.

---

## Prerequisites

Before starting, ensure the following are installed on your machine:

* **Python** (version defined in `pyproject.toml`)
* **Poetry** (used for dependency and environment management)
* **Git**

Using the same Python and Poetry versions across the team helps avoid subtle environment-related issues.

---

## Repository Setup

### 1. Clone the Repository

```bash
git clone https://github.com/rohitlingarker/bfsi-agents
cd agents/<agent_name>_agent
```

This clones the central `bfsi-agents` repository and navigates into the specific agent you want to work on.

Each agent lives in its own folder under `agents/`, but follows the same structure and setup process.

---

### 2. Install Dependencies

```bash
poetry install
```

What this does:

* Creates a virtual environment for the project
* Installs all dependencies defined in `pyproject.toml`
* Uses `poetry.lock` to ensure exact versions

This step is required only once unless dependencies change.

---

### 3. Verify the Environment

```bash
poetry env info
```

This command confirms:

* Which Python interpreter is being used
* Where the virtual environment is located

It’s a useful first check if something behaves unexpectedly.

---

## Running the Application Locally

All application commands are run through Poetry to ensure the correct environment and dependencies are used.

### Development Mode

To start the application locally in development mode:

```bash
poetry run dev
```

This command is intended for local development and typically enables faster feedback, reloads, or additional logging as configured by the agent.

---

### Production Mode

To run the application in production mode:

```bash
poetry run prod
```

This mirrors how the service is expected to run in production environments.

Using these standardized commands keeps local, CI, and production execution consistent and predictable.

---

## Environment Configuration

Most configuration is provided via environment variables.

Typical setup steps:

* Copy `.env.example` to `.env` (if present)
* Update values as needed for local development

Configuration loading is handled centrally (usually in `src/core/config.py`).

Keeping configuration outside code makes the service easier to run across environments.

---

## Running Tests

Tests should always be executed inside the Poetry environment.

```bash
poetry run pytest
```

This ensures tests use the same dependencies and settings as the application.

---

## Common Issues and Tips

* **Dependency errors**: Run `poetry install` again and ensure Python version matches `pyproject.toml`
* **Command not found**: Make sure commands are run via `poetry run`
* **Unexpected behavior**: Verify the active virtual environment with `poetry env info`

Most setup issues are related to environment mismatches, and Poetry helps surface these early.

---

## Summary

This setup process is intentionally simple:

1. Clone the repo
2. Install dependencies with Poetry
3. Run the service using Poetry-managed commands

Following this workflow keeps development environments consistent, reduces friction during onboarding, and supports smooth long-term maintenance and refactoring.
