# KYC Agent

`kyc_agent` performs identity verification and customer due diligence after intake. It runs a LangGraph-based parallel KYC workflow, persists KYC cases and audit artifacts, and returns a structured pass/fail/manual-review style decision payload for downstream decisioning.

## Responsibilities

- Accept KYC trigger requests for a loan applicant.
- Enforce idempotent KYC execution.
- Run normalization, SSN, address, AML, and contact verification steps.
- Aggregate risk using a rule-driven policy engine.
- Persist KYC cases, identity checks, and related audit artifacts.
- Return a KYC decision plus supporting explanation and raw credit data used downstream.

## Main Entry Points

- App factory: `src/app.py`
- Uvicorn entrypoint: `src/main.py`
- CLI commands: `src/cli.py`
- Active route: `src/api/v1/kyc_routes/kyc_routes.py`
- Main orchestration service: `src/services/kyc_services/kyc_orchestrator.py`
- LangGraph definition: `src/workflows/decision_flow.py`

## API Surface

Primary routes:

- `GET /`
- `GET /health`
- `POST /verify`

There is also an older route module at `src/api/routes.py` exposing `POST /kyc/execute`, but the current orchestrator integration uses `POST /verify`.

## Workflow

The active graph fans out after normalization and runs several checks in parallel:

- SSN validation
- address verification
- AML screening
- contact verification

Those results feed into the risk aggregator, which loads policy rules from `src/workflows/kyc_engine/rules/kyc_rules.yaml`, computes a confidence score, and produces the final KYC result. The graph then builds a human-readable explanation.

## Persistence

The agent persists KYC execution data through repository classes under `src/repositories/kyc_repo/`, including:

- KYC cases
- request/response idempotency state
- identity checks
- risk decisions and audit payloads

Alembic migrations live under `alembic/`.

## Running Locally

From `agents/kyc_agent`:

```bash
poetry install
poetry run dev
```

Useful commands:

```bash
poetry run prod
poetry run test
poetry run migrate
poetry run migration "describe change"
poetry run lint
```

The CLI currently starts the service on port `8001`.

## Tests

The test suite includes KYC flow coverage, identity and address verification checks, idempotency behavior, liveness verification helpers, and fuzz tests.

```bash
poetry run test
```

## Current Notes

- Redis-backed idempotency plumbing exists in the app and middleware layers.
- The codebase contains both older and newer orchestration paths; `KYCOrchestratorService` is the main path to follow for current integrations.
- Some planned graph branches such as human review and face verification are present in the repo but not fully wired into the active graph.
