# Pipeline observability (LLM + full review pipeline)

**Status:** **P0 shipped** on `main` ([#92](https://github.com/raimondskrauklis/revy/pull/92), `be16bc7`). **P0 behavioral PASS** on staging dogfood [#93](https://github.com/raimondskrauklis/revy/pull/93). **Next:** `phase-execution` from [P1](./waves/PIPELINE_OBSERVABILITY_P1_EXECUTION.md).

| Doc | Purpose |
|-----|---------|
| [PIPELINE_OBSERVABILITY_FINDINGS.md](./PIPELINE_OBSERVABILITY_FINDINGS.md) | Baseline — OTel-aligned metric model, gaps, catalog |
| [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](./PIPELINE_OBSERVABILITY_GENERAL_PLAN.md) | Phased goals (P0–P5) |
| [waves/PIPELINE_OBSERVABILITY_EXECUTION.md](./waves/PIPELINE_OBSERVABILITY_EXECUTION.md) | Execution index + LOOP order (P0–P5) |
| [PIPELINE_OBSERVABILITY_STAGING_VALIDATION.md](./PIPELINE_OBSERVABILITY_STAGING_VALIDATION.md) | P0 behavioral PASS — dogfood [#93](https://github.com/raimondskrauklis/revy/pull/93) |
| [reviews/architecture-peer-review/](./reviews/architecture-peer-review/README.md) | Architecture peer review — pass 2 (**BLOCK: no**) |
| [reviews/execution-peer-review/](./reviews/execution-peer-review/README.md) | Execution peer review — pass 2 (**BLOCK: no**) |

## Execution (LOOP)

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | Schema, recorder, commit graph, pricing, purge | [P0](./waves/PIPELINE_OBSERVABILITY_P0_EXECUTION.md) | Done (`be16bc7`) |
| P1 | Moonshot, Anthropic judge, Voyage instrumentation | [P1](./waves/PIPELINE_OBSERVABILITY_P1_EXECUTION.md) | pending |
| P2 | Incremental pipeline trace (`processing` → terminal) | [P2](./waves/PIPELINE_OBSERVABILITY_P2_EXECUTION.md) | pending |
| P3 | Rollups, `estimated_usd`, API exposure | [P3](./waves/PIPELINE_OBSERVABILITY_P3_EXECUTION.md) | pending |
| P4 | Staging metrics script + log alias sunset | [P4](./waves/PIPELINE_OBSERVABILITY_P4_EXECUTION.md) | pending |
| P5 | OTel OTLP export + doc sync | [P5](./waves/PIPELINE_OBSERVABILITY_P5_EXECUTION.md) | pending |

**Scope:** End-to-end Revy review pipeline with **tokens, latency, finish_reason, and typed failures** on every LLM call and stage. **Estimated cost** is informational only; **vendor billing APIs** (Moonshot/Anthropic/Voyage) for real spend are **deferred** (PO-Q12) — not CSV.

**Industry anchor:** [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) (`gen_ai.operation.name`, `gen_ai.usage.*`, `gen_ai.response.finish_reasons`).

**Related:** [judge-json-contract](../judge-json-contract/) · [staging-validation](../staging-validation/) · [JUDGE_STAGING_SPEND_INVESTIGATION_FINDINGS.md](../judge/JUDGE_STAGING_SPEND_INVESTIGATION_FINDINGS.md)
