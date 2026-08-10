# Pipeline observability — execution index

**Baseline:** [PIPELINE_OBSERVABILITY_FINDINGS.md](../PIPELINE_OBSERVABILITY_FINDINGS.md)  
**General plan:** [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](../PIPELINE_OBSERVABILITY_GENERAL_PLAN.md)  
**Architecture peer review:** [pass-02](../reviews/architecture-peer-review/pass-02-2026-08-10.md) — **BLOCK: no**

**Authority:** findings §Commit graph, §Decisions registry (PO-Q1–Q19).

## Locked decisions (all phases)

- Commit graph boundaries #1–#6 with per-boundary `commit()` — not `flush()` alone.
- `failure_class` shared taxonomy on runs + attempts + logs.
- `pipeline_run_id` required when writing attempt rows; skip embed attempts without pipeline run (PO-Q16).
- `trigger_source` on review runs set in `create_review_run` from completed index job (PO-Q15).
- **Recorder sessions (PO-Q17):** attempt rows via dedicated `get_db_context()`; checkpoint on shared session + `refresh(run)`.
- **Latency SSOT (PO-Q18):** `attempts.wait_ms` for percentiles; `timing_stats.review_llm_wait_ms` as run mirror.
- **OTLP hooks (PO-Q19):** idempotent export at review + reconcile + publish terminal commits.
- Bedrock not dropped; `bedrock_review.py` instrumentation deferred (PO-Q13).
- HTTP timeout headroom shipped PR #90 — not re-implemented.

## LOOP order

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | Schema, recorder, commit graph, pricing, purge | [P0](./PIPELINE_OBSERVABILITY_P0_EXECUTION.md) | Done (`be16bc7`, [#92](https://github.com/raimondskrauklis/revy/pull/92)) |
| P1 | Moonshot, Anthropic judge, Voyage instrumentation | [P1](./PIPELINE_OBSERVABILITY_P1_EXECUTION.md) | pending |
| P2 | Incremental pipeline trace (`processing` → terminal) | [P2](./PIPELINE_OBSERVABILITY_P2_EXECUTION.md) | pending |
| P3 | Rollups, `estimated_usd`, API exposure | [P3](./PIPELINE_OBSERVABILITY_P3_EXECUTION.md) | pending |
| P4 | Staging metrics script + log alias sunset | [P4](./PIPELINE_OBSERVABILITY_P4_EXECUTION.md) | pending |
| P5 | OTel OTLP export + doc sync | [P5](./PIPELINE_OBSERVABILITY_P5_EXECUTION.md) | pending |

**Depends (hard gates):** P1,P2 → P0 · P3 → P1+P2 · P4 → P3 · P5 → P3.

**Next:** `phase-execution` from [P1](./PIPELINE_OBSERVABILITY_P1_EXECUTION.md). **Human gate:** apply migration `0031` on staging before P1.
