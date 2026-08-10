# Model run capture — execution index

Linear **phase-execution** order. General plan: [`../MODEL_RUN_CAPTURE_GENERAL_PLAN.md`](../MODEL_RUN_CAPTURE_GENERAL_PLAN.md).

**Authority:** [`../MODEL_RUN_CAPTURE_FINDINGS.md`](../MODEL_RUN_CAPTURE_FINDINGS.md) (MRC-Q1–Q10), [`../../review-pipeline/pipeline-observability/PIPELINE_OBSERVABILITY_GENERAL_PLAN.md`](../../review-pipeline/pipeline-observability/PIPELINE_OBSERVABILITY_GENERAL_PLAN.md) (PO-P1.4 Voyage contract).

| Phase | File | Status |
|-------|------|--------|
| MRC-P0 — Index embedding identity | [MODEL_RUN_CAPTURE_P0_EXECUTION.md](./MODEL_RUN_CAPTURE_P0_EXECUTION.md) | shipped |
| MRC-P1 — Attempt rows + judge/publish step models | [MODEL_RUN_CAPTURE_P1_EXECUTION.md](./MODEL_RUN_CAPTURE_P1_EXECUTION.md) | pending |
| MRC-P2 — `models_snapshot` + staging metrics | [MODEL_RUN_CAPTURE_P2_EXECUTION.md](./MODEL_RUN_CAPTURE_P2_EXECUTION.md) | pending |
| MRC-P3 — API exposure + staging sign-off | [MODEL_RUN_CAPTURE_P3_EXECUTION.md](./MODEL_RUN_CAPTURE_P3_EXECUTION.md) | pending |

**LOOP order:** MRC-P0 → MRC-P1 → MRC-P2 → MRC-P3 (strict).

**Sibling coordination:** MRC-P1.1 implements PO-P1.4 Voyage `index_embed` contract if not already on `main`; do not fork attempt schema.

**Pre-flight:** Findings baseline-ready; architecture peer-review pass 1 incorporated; execution peer-review pass 1δ **BLOCK: no** (2026-08-10).
