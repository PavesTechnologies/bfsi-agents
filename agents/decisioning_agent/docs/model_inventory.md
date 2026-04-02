# Model Inventory

## Scope
This inventory covers the active underwriting path in `agents/decisioning_agent`.

## Deterministic Decision Components
- `src/domain/calculators/dti.py`
  - Computes debt-to-income ratios and affordability flags.
- `src/domain/calculators/credit_banding.py`
  - Maps bureau score to deterministic score bands and limit bands.
- `src/domain/calculators/public_records.py`
  - Evaluates bankruptcy/public-record severity and hard-decline flags.
- `src/domain/calculators/utilization.py`
  - Computes revolving utilization metrics and adjustment factors.
- `src/domain/calculators/inquiry_velocity.py`
  - Computes inquiry counts and inquiry penalty factors.
- `src/domain/calculators/behavior.py`
  - Computes delinquency and charge-off risk metrics.
- `src/domain/calculators/exposure.py`
  - Computes exposure risk and monthly obligation estimates.
- `src/domain/calculators/counter_offer.py`
  - Generates deterministic counter-offer options.
- `src/domain/decisioning/decision_engine.py`
  - Owns final approve/decline/counter-offer/refer-to-human routing.
- `src/domain/reason_codes/reason_registry.py`
  - Registry of allowed adverse-action reason keys and codes.
- `src/domain/reason_codes/reason_selector.py`
  - Deterministic decline-reason selection from triggered policy conditions.
- `src/domain/decisioning/decision_submission.py`
  - Constrained boundary enforcing valid principal reason selection.

## LLM-Tied Components
- `src/core/versioning.py`
  - Carries runtime `model_version` and `prompt_version`.
- `src/services/decision_model/decision_parser.py`
  - Defines structured output contract consumed by deterministic routing.

## Audit and Monitoring Components
- `src/domain/audit/narrative_builder.py`
  - Produces normalized audit narratives per underwriting decision.
- `src/utils/audit_decorator.py`
  - Writes raw node debug payloads plus compact compliance summaries.
- `src/services/monitoring/decision_metrics.py`
  - Normalizes underwriting outcomes into monitoring telemetry.
- `src/services/validation/release_report.py`
  - Builds release validation summaries.

## Control Notes
- Final underwriting outcomes are deterministic.
- Prompt/model versions are persisted with underwriting decisions.
- Human review is a first-class outcome and is persisted separately.
- Monitoring snapshots are persisted separately from underwriting decisions.
