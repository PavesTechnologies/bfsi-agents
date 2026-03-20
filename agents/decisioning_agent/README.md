# Decisioning Agent

`decisioning_agent` is the underwriting service in the BFSI pipeline. It ingests the KYC-cleared applicant's credit and income context, runs a parallel risk-evaluation graph, applies an LLM-backed decision step with deterministic fallback logic, and persists the final underwriting decision for downstream disbursement.

## Responsibilities

- Accept underwriting requests from the orchestrator or other internal callers.
- Enforce idempotent underwriting execution.
- Run parallel risk analysis over credit score, public records, utilization, exposure, payment behavior, inquiry velocity, and income.
- Aggregate those signals into an underwriting risk score and risk tier.
- Produce an `APPROVE`, `COUNTER_OFFER`, or `DECLINE` decision.
- Persist underwriting decisions and service audit logs.

## Main Entry Points

- App factory: `src/app.py`
- Uvicorn entrypoint: `src/main.py`
- CLI commands: `src/cli.py`
- Route module: `src/api/routes.py`
- Main service: `src/services/underwriting_service.py`
- LangGraph definition: `src/workflows/decision_flow.py`

## API Surface

Primary routes:

- `GET /`
- `POST /underwrite`

The service resolves or propagates a correlation ID and returns a typed `UnderwritingResponse`.

## Workflow

The underwriting graph is defined in `src/workflows/decision_flow.py` and follows this shape:

1. PII deletion or masking
2. Parallel risk-signal extraction
3. Risk aggregation
4. LLM decision step
5. Conditional counter-offer routing
6. Final LOS-style response composition

Important node groups live under `src/workflows/decision_engine/nodes/`.

## LLM Integration

The graph's decision step uses shared executor code under `src/services/llm_executor.py` and model-specific prompt/parser packages under `src/services/*_model/`.

Current state:

- `src/adapters/llm/openai_adapter.py` is still a placeholder adapter.
- The decision layer includes deterministic fallback behavior when an LLM result is unavailable or unusable.

## Persistence

The service writes underwriting-related records through repository classes under `src/repositories/`, including:

- `underwriting_decisions`
- `underwriting_idempotency`
- `service_audit_logs`

Alembic migrations live under `alembic/`.

## Running Locally

From `agents/decisioning_agent`:

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

Note: the CLI currently starts this service on port `8001`, while the repo-level orchestrator defaults expect decisioning on `8002`. If you run the full stack locally, align the port configuration through environment variables or CLI changes before wiring services together.

## Tests

The test suite covers response contracts, request context handling, hash/idempotency behavior, and repository/audit logic.

```bash
poetry run test
```

## Current Notes

- This is one of the more mature agents in the repo from a workflow and persistence perspective.
- The service records both idempotency state and service-level audit logs around the underwriting operation.
- The final response payload is designed to feed directly into the disbursement agent.
