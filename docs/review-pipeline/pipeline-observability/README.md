# Pipeline observability (LLM + full review pipeline)

**Status:** execution plan peer-reviewed — ready for `phase-execution`.

| Doc | Purpose |
|-----|---------|
| [PIPELINE_OBSERVABILITY_FINDINGS.md](./PIPELINE_OBSERVABILITY_FINDINGS.md) | Baseline — OTel-aligned metric model, gaps, catalog |
| [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](./PIPELINE_OBSERVABILITY_GENERAL_PLAN.md) | Phased goals (P0–P5) |
| [waves/PIPELINE_OBSERVABILITY_EXECUTION.md](./waves/PIPELINE_OBSERVABILITY_EXECUTION.md) | Execution index + LOOP order (P0–P5) |
| [reviews/architecture-peer-review/](./reviews/architecture-peer-review/README.md) | Architecture peer review — pass 2 (**BLOCK: no**) |
| [reviews/execution-peer-review/](./reviews/execution-peer-review/README.md) | Execution peer review — pass 2 (**BLOCK: no**) |

**Scope:** End-to-end Revy review pipeline with **tokens, latency, finish_reason, and typed failures** on every LLM call and stage. **Estimated cost** is informational only; **vendor billing APIs** (Moonshot/Anthropic/Voyage) for real spend are **deferred** (PO-Q12) — not CSV.

**Industry anchor:** [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) (`gen_ai.operation.name`, `gen_ai.usage.*`, `gen_ai.response.finish_reasons`).

**Related:** [judge-json-contract](../judge-json-contract/) · [staging-validation](../staging-validation/) · [JUDGE_STAGING_SPEND_INVESTIGATION_FINDINGS.md](../judge/JUDGE_STAGING_SPEND_INVESTIGATION_FINDINGS.md)
