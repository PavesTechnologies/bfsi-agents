# Agentic Platform (Mono-Repo)

This repository contains a **mono-repo for agentic microservices** used to build
AI-driven workflows (BFSI / enterprise use cases).

Each **agent is an independent microservice**, but all agents follow the **same
architecture, rules, and standards** defined in this repository.

This repo is designed to:
- enable fast experimentation with agentic workflows
- enforce architectural discipline
- scale to multiple banking / financial use cases
- avoid early fragmentation into many repos

---

## Repository Structure (High Level)

```
agentic-platform/
├── agents/          # All agent microservices
├── shared/          # Stable shared utilities (minimal, reusable)
├── infra/           # Platform-level infra (Docker, K8s, Terraform, CI)
├── tools/           # Dev tools & generators
├── docs/            # Architecture & coding standards
└── README.md
```

---

## Prerequisites (Mandatory)

Install these **before doing anything**:

- Python **3.11.x**
- Git
- Poetry

Install Poetry:
```bash
pip install poetry
```

> ❗ Do NOT install Python dependencies globally  
> ❗ Do NOT skip virtual environments  
> ❗ Each agent has its own isolated environment  

---

# 1️⃣ Working on an Existing Agent

### Step 1: Go to the agent directory
```bash
cd agents/intake_agent
```

(Replace `intake_agent` with the agent you are working on.)

---

### Step 2: Install dependencies (first time only)
```bash
poetry install
```

This creates an isolated virtual environment **for this agent only**.

---

### Step 3: Run the agent
```bash
poetry run dev
```

---


### Step 5: Run tests
```bash
poetry run test
```

---

## Rules When Working on an Agent

- Each agent has its **own `pyproject.toml`**
- Each agent has its **own virtual environment**
- Never install Python packages globally
- Never bypass Poetry
- Never modify another agent unless required
- Follow the folder responsibility rules strictly

---

# 2️⃣ Creating a New Agent

❌ **Do NOT create agents manually**

Always use the generator.

---

### Step 1: From repo root
```bash
python tools/generators/new_agent.py underwriting_agent
```

Agent name rules:
- must be `snake_case`
- must end with `_agent`
- examples: `intake_agent`, `kyc_agent`, `fraud_agent`

---

### Step 2: Move into the new agent
```bash
cd agents/underwriting_agent
```

---

### Step 3: Install dependencies
```bash
poetry install
```

The agent is now ready for development.

---

# 3️⃣ Standard Agent Folder Structure

Every agent **must** follow this structure:

```
agents/<agent_name>/
├── src/
│   ├── api/           # HTTP endpoints (FastAPI)
│   ├── core/          # config, logging, security, telemetry
│   ├── domain/        # business rules & invariants (MOST IMPORTANT)
│   ├── models/        # request / response / event schemas
│   ├── services/      # step execution & orchestration
│   ├── adapters/      # external systems (OCR, DB, APIs, queues)
│   ├── workflows/     # LangGraph control flow
│   ├── repositories/ # persistence logic
│   ├── utils/         # pure helpers (no business logic)
│   ├── app.py
│   └── main.py
├── tests/
├── infra/
├── pyproject.toml
└── README.md
```

This structure is **non-negotiable**.

---

# 4️⃣ Where Does Logic Go?

Use this table when writing code.

| Folder | Responsibility |
|------|---------------|
| `api/` | Entry point only (no business logic) |
| `domain/` | Business truth (rules, validation, policies) |
| `services/` | Execute steps & coordinate work |
| `adapters/` | Talk to external systems |
| `workflows/` | Decide execution path (LangGraph) |
| `repositories/` | Read/write persistence |
| `models/` | Data shapes & contracts |
| `utils/` | Pure helpers |
| `core/` | Cross-cutting infra concerns |

### Golden Rule
> **Domain decides truth**  
> **Services do work**  
> **Workflows decide paths**  
> **Adapters talk to the outside world**

---

# 5️⃣ Workflow vs Service (Mental Model)

- **Service** → *How do I perform this step?*
- **Workflow** → *What happens next?*

Example:
- Service: extract document
- Workflow: retry → escalate → stop

---

# 6️⃣ Git & Repo Rules

- Single `.gitignore` at repo root
- `.gitkeep` files preserve empty folders
- Do NOT commit `.venv/`
- Do NOT commit secrets
- Always commit `pyproject.toml` and `poetry.lock`

---

# 7️⃣ Shared Code (`shared/`)

Use `shared/` **only when**:
- code is used by **2+ agents**
- code is stable
- code is not agent-specific

If code changes frequently → keep it inside the agent.

---

# 8️⃣ Common Mistakes (Avoid These)

❌ Business logic in `api/`  
❌ External calls in `domain/`  
❌ Workflow calling adapters directly  
❌ Manual agent creation  
❌ One virtual environment for multiple agents  

---

## Final Rule (Memorize This)

> **Consistency beats cleverness.  
Follow the structure.**

If you are unsure where something belongs, ask before coding.
