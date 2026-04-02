# Control Matrix

| Control Objective | Implementation | Evidence |
| --- | --- | --- |
| Deterministic underwriting math | Ratio, score, utilization, inquiry, behavior, exposure, and counter-offer logic live in Python calculators. | `src/domain/calculators/*` |
| Deterministic final decisioning | Final routing is owned by `decision_engine.py`, not prompt text. | `src/domain/decisioning/decision_engine.py` |
| Controlled adverse-action mapping | Declines use registry-backed reason selection and constrained submission validation. | `src/domain/reason_codes/*`, `src/domain/decisioning/decision_submission.py` |
| Human-in-the-loop routing | `REFER_TO_HUMAN` is an explicit underwriting outcome with review packet generation and persistence. | `src/workflows/decision_flow.py`, `src/services/underwriting_human_review_service.py` |
| Policy/version traceability | Policy/model/prompt version metadata is propagated into state, responses, and persistence. | `src/services/underwriting_service.py`, `src/core/versioning.py` |
| Audit narrative | Structured underwriting audit narrative is persisted with decisions. | `src/domain/audit/narrative_builder.py`, `src/repositories/underwriting_repository.py` |
| Node-level audit | Raw input/output state and compact node summaries are logged. | `src/utils/audit_decorator.py`, `src/models/node_audit.py` |
| Monitoring and fairness analysis | Telemetry export, disparate-impact analysis, reason distribution, drift, and alerts exist in code. | `src/services/monitoring/*`, `src/services/fairness/*` |
| Monitoring persistence | Monitoring snapshots are persisted and retrievable by segment. | `src/services/underwriting_monitoring_service.py`, `src/models/underwriting_monitoring_snapshot.py` |

## Residual Gaps
- Monitoring snapshot generation is manual or API-driven; it is not yet scheduler-driven.
- Governance approval workflow for policy/model/prompt promotion is still procedural rather than enforced in code.
- Retrieval-grounded policy citation is not yet part of a formal validation gate.
