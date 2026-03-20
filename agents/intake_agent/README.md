# Intake Agent

`intake_agent` is the front door for loan applications in the `bfsi-agents` platform. It accepts application payloads from the UI or upstream callers, normalizes and validates applicant data, persists the LOS records, stores request metadata, and exposes supporting flows such as document upload, human-in-the-loop handling, and loan query endpoints.

## Responsibilities

- Accept loan application submissions.
- Normalize request payloads into the repo's canonical intake models.
- Run blocking and non-blocking validations for applicants and related entities.
- Persist loan applications, applicants, addresses, employment, income, assets, liabilities, callbacks, metadata, and validation artifacts.
- Enforce request-level idempotency.
- Expose auxiliary APIs for document upload, human review, and loan queries.
- Trigger the orchestrator after intake is complete.

## Main Entry Points

- App factory: `src/app.py`
- Uvicorn entrypoint: `src/main.py`
- CLI commands: `src/cli.py`
- Core intake route: `src/api/v1/intake_routes/loan_intake_routes.py`
- Main service: `src/services/intake_services/loan_intake_service.py`

## API Surface

The app mounts multiple routers, but the most important intake routes are:

- `GET /loan_intake/check`
- `POST /loan_intake/submit_application`
- `POST /loan_intake/trigger_orchestrator`

Additional routers are mounted for:

- health checks
- document upload
- human-in-loop workflows
- loan query flows

## Processing Flow

1. The client submits a `LoanIntakeRequest`.
2. Blocking validations run before idempotency is finalized.
3. The request is normalized through the domain normalization layer.
4. Loan, applicant, address, employment, income, asset, and liability records are persisted.
5. Non-blocking validation issues are stored and returned in the response payload.
6. The request is marked complete in the idempotency store.
7. A separate async intake-processing path exists for callback-based work.

## Persistence

This agent primarily owns the intake-side LOS records described in the repo database docs, including:

- `loan_application`
- `applicant`
- `address`
- intake idempotency records
- validation and metadata-related tables used by this service

Alembic migrations live under `alembic/`.

## Running Locally

From `agents/intake_agent`:

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

The CLI currently starts the service on port `8000`.

## Tests

The test suite covers API routes, integration flows, validation logic, enrichment adapters, output schema generation, and callback/finalization behavior. Run:

```bash
poetry run test
```

## Current Notes

- The repository contains substantial intake-domain code beyond simple application submission, including OCR, document classification, enrichment adapters, and output finalization.
- The async processor in `src/services/intake_processor.py` is still mostly placeholder logic and currently simulates processing before firing a success callback.
- The app configures CORS for local UI development and a hosted frontend origin in `src/app.py`.
