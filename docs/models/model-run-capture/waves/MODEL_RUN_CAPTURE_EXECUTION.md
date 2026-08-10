# Model run capture — execution index

**Baseline:** [MODEL_RUN_CAPTURE_FINDINGS.md](../MODEL_RUN_CAPTURE_FINDINGS.md)  
**General plan:** [MODEL_RUN_CAPTURE_GENERAL_PLAN.md](../MODEL_RUN_CAPTURE_GENERAL_PLAN.md)  
**Architecture peer review:** [pass-01](../reviews/architecture-peer-review/pass-01-2026-08-10.md) — **BLOCK: no**  
**Execution peer review:** [pass-01δ](../reviews/execution-peer-review/pass-01-2026-08-10-delta.md) — **BLOCK: no**

**Authority:** findings §Decisions registry (MRC-Q1–Q10).

## Locked decisions (all phases)

- Capture model at HTTP/call site — never re-read `settings` in trace writers (MRC findings §1).
- `embed_batches=0` → no imputed embedding model (MRC-Q8).
- `models_snapshot` terminal write after publish or pipeline failure hook (MRC-Q9).
- PO-P1.4 contract for Voyage `index_embed` attempts; MRC verifies `request_model` matches index manifest (MRC-Q10).
- Share `github_llm_call_attempts` with pipeline observability — no parallel table (MRC-Q5).
- Manual-index jobs without `pipeline_run_id` — skip embed attempts (MRC-Q6 / PO-Q16).

## LOOP order

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| MRC-P0 | Index manifest + step embedding identity | [P0](./MODEL_RUN_CAPTURE_P0_EXECUTION.md) | shipped |
| MRC-P1 | Attempt rows + judge/publish step models | [P1](./MODEL_RUN_CAPTURE_P1_EXECUTION.md) | shipped |
| MRC-P2 | `models_snapshot` + staging metrics by model | [P2](./MODEL_RUN_CAPTURE_P2_EXECUTION.md) | in progress (P2.1 shipped) |
| MRC-P3 | API exposure + staging sign-off | [P3](./MODEL_RUN_CAPTURE_P3_EXECUTION.md) | pending |

**Next after execution peer-review:** `phase-execution` from [MODEL_RUN_CAPTURE_P0_EXECUTION.md](./MODEL_RUN_CAPTURE_P0_EXECUTION.md) (execution peer-review pass 1δ — BLOCK: no).
