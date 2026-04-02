# Validation Plan

## Objective
Provide a reviewable validation pack for deterministic underwriting, adverse-action mapping, auditability, HITL routing, and monitoring.

## Core Validation Areas
1. Deterministic decisioning
   - Same inputs produce same outcomes.
   - LLM version metadata does not change final business routing.
2. Adverse-action controls
   - Declines emit exactly two valid principal reason keys.
   - Customer-facing notice fields are present on decline responses.
3. Auditability
   - Policy/model/prompt versions persist with underwriting decisions.
   - Audit narrative captures calculations, routing, and triggered reason keys.
   - Node audit logs preserve raw payloads and compact compliance summaries.
4. Human review routing
   - Missing or unverifiable income routes to manual review.
   - Borderline deterministic cases route to manual review with reviewer packet.
5. Monitoring and fairness
   - Telemetry export is stable.
   - Disparate-impact, drift, and reason-distribution calculations are reproducible.
   - Monitoring alerts fire when thresholds are breached.

## Repo Test Coverage
- `tests/test_decision_engine.py`
- `tests/test_decline_reason_mapping.py`
- `tests/test_audit_narrative.py`
- `tests/test_node_audit_logging.py`
- `tests/test_human_review_routing.py`
- `tests/test_monitoring_and_fairness.py`
- `tests/test_underwriting_monitoring_service.py`
- `tests/test_validation_pack.py`

## Recommended Release-Gate Command
```powershell
$env:DATABASE_GENERIC='postgresql+asyncpg://test:test@localhost:5432/testdb'; poetry run pytest tests/test_decision_engine.py tests/test_decline_reason_mapping.py tests/test_audit_narrative.py tests/test_node_audit_logging.py tests/test_human_review_routing.py tests/test_monitoring_and_fairness.py tests/test_underwriting_monitoring_service.py tests/test_validation_pack.py
```

## Expected Evidence Bundle
- Generated test results from the release-gate command
- Policy version, prompt version, and model version values used for the release
- Sample approve, decline, counter-offer, and refer-to-human responses
- Monitoring snapshot from a representative evaluation batch
