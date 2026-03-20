# Disbursment Agent

`disbursment_agent` is the final execution stage in the loan pipeline. It takes the output of underwriting, validates whether the decision can move forward, generates a repayment schedule, simulates a fund transfer through a banking gateway abstraction, records transition history, and returns a disbursement receipt.

## Responsibilities

- Accept approved or counter-offer-derived loan decisions.
- Enforce idempotent execution for disbursement requests.
- Validate the incoming decision payload before money movement logic runs.
- Generate repayment schedules and receipt data.
- Execute transfer logic through a banking gateway abstraction.
- Persist disbursement records, transition logs, idempotency state, and service audit logs.

## Main Entry Points

- App factory: `src/app.py`
- Uvicorn entrypoint: `src/main.py`
- CLI commands: `src/cli.py`
- Route module: `src/api/routes.py`
- Main service: `src/services/orchestrator.py`
- LangGraph definition: `src/workflows/decision_flow.py`

## API Surface

Primary routes:

- `GET /`
- `POST /disburse`

The API accepts a `DisbursementRequest` and returns the final receipt payload produced by the graph.

## Workflow

The disbursement graph is intentionally compact:

1. validate decision
2. generate repayment schedule
3. execute fund transfer
4. generate receipt

If validation fails, the graph skips directly to receipt generation with the rejection or error context.

## Banking Gateway

The current transfer integration in `src/services/banking_gateway.py` is a mock implementation. It simulates an external core-banking or payments API and returns a synthetic transaction ID and transfer status.

## Persistence

The service persists through repository classes under `src/repositories/`, including:

- `disbursement_records`
- `disbursement_idempotency`
- `disbursement_transition_logs`
- `service_audit_logs`

Alembic migrations live under `alembic/`.

## Running Locally

From `agents/disbursment_agent`:

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
```

Note: the CLI currently starts this service on port `8002`, while the repo-level orchestrator defaults expect disbursement on `8003`. If you run the full stack locally, update environment configuration or ports so the orchestrator points at the actual service.

## Tests

The tests cover transfer logic, idempotency behavior, transition handling, request context, repository contracts, and service audit persistence.

```bash
poetry run test
```

## Current Notes

- The package name is spelled `disbursment_agent` across the repo and should be treated as canonical for imports and paths.
- The workflow and persistence layers are in relatively good shape, but the actual banking integration is still mocked.
- Transition history is explicitly derived and stored so downstream systems can audit state changes over time.
