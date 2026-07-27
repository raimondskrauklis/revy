# Review quality program (post-R8)

**Status:** findings + general plans + execution locked (2026-07-27). **Ship:** one PR `feat/review-quality` → tag `review-quality-v1`. **Next:** `phase-execution` (execution peer-review complete).

Post-R8 program: **diff-first review**, **pipeline explainability**, Greptile-shaped **GitHub publish**, incremental index (C1), evidence + grounding, resolution metrics. R0–R8 = core pipeline.

**Prerequisite:** R0–R8 on `main`; autostart **staging e2e gate** (AS2) in RQ8 human gate.

---

## Docs (order)

| Step | Doc | Purpose |
|------|-----|---------|
| 1 | [REVIEW_QUALITY_FINDINGS.md](./REVIEW_QUALITY_FINDINGS.md) | Baseline + Q-registry — **start here** |
| 2 | [REVIEW_QUALITY_GENERAL_PLAN.md](./REVIEW_QUALITY_GENERAL_PLAN.md) | Index → per-slice general plans |
| 3 | [R1](./REVIEW_QUALITY_R1_DIFF_AND_TRACE_GENERAL_PLAN.md) · [R2](./REVIEW_QUALITY_R2_INCREMENTAL_INDEX_GENERAL_PLAN.md) · [R3](./REVIEW_QUALITY_R3_GITHUB_PUBLISH_GENERAL_PLAN.md) · [R4](./REVIEW_QUALITY_R4_EVIDENCE_JUDGE_GENERAL_PLAN.md) · [R5](./REVIEW_QUALITY_R5_RESOLUTION_METRICS_GENERAL_PLAN.md) | Slice general plans (one PR) |
| 4 | [REVIEW_QUALITY_EXECUTION.md](../waves/REVIEW_QUALITY_EXECUTION.md) | RQ0–RQ8 — **`phase-execution`** on `feat/review-quality` (peer-reviewed) |
| — | [REVIEW_QUALITY_PEER_REVIEW.md](./REVIEW_QUALITY_PEER_REVIEW.md) | Architecture peer review + pre-execution locks |
| — | [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) | **Post-v1 strategy** — LSP defer, RQ-STRUCT-1/2, Greptile parity |
| — | [REVIEW_QUALITY_REVIEW_CONTEXT.md](./REVIEW_QUALITY_REVIEW_CONTEXT.md) | **Post-v1 strategy** — Greptile/Bugbot planning-doc wiring, RQ-RC-1 |

---

## Tracks

| Track | Focus | Slice |
|-------|--------|-------|
| **D** — Diff-first | D13 hybrid index; diff context pack; `full` parallel | R1 |
| **O** — Explainability | Pipeline trace; `items_view` API; purge | R1 |
| **I + C1** — Incremental | Copy-forward; delta embed | R2 |
| **G** — GitHub publish | Greptile comment; G3 split bodies | R3 |
| **E** — Evidence | Snippet; grounding judge | R4 |
| **M + G9** — Metrics | `resolution_status` → publish prose | R5 |
| **A** — Agents | Defer R6+ |
| **RC** — Review context | Greptile/Bugbot ↔ planning docs; RQ0 ships v0; **RQ-RC-1** post-v1 |

---

## Locked decisions (summary)

| Topic | Resolution |
|-------|------------|
| Ship | One PR, one execution file (S1–S2) |
| Autostart profile | `standard` → `diff` until workspace profile setting (AS1) |
| Autostart bug | Staging e2e gate (AS2); fix only if gate fails |
| Diff index | Compare for list+diff; tarball for changed paths only (D13) |
| Pipeline read | `items_view` read; `admin_users` retention (O9) |
| Fingerprint | D10 in same PR |
| Fixed prose | R5 owns status; R3 reads (G9) |
| LSP / cross-file | Defer full LSP v1; north star **graph + agents** (SC8); bridge **RQ-STRUCT-1** v1.1 — [structural context](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| PR review context | RQ0 wires `.greptile/files.json` + `.cursor/BUGBOT.md` (RC0); improve in **RQ-RC-1** — [review context](./REVIEW_QUALITY_REVIEW_CONTEXT.md) |

---

## Related

| Doc | Role |
|------|------|
| [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) | Greptile + iterative review |
| [REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md](../REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md) | Smoke #44 — why diff-first |
| [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) | LSP defer; cross-file roadmap (RQ-STRUCT-1/2) |
| [REVIEW_QUALITY_REVIEW_CONTEXT.md](./REVIEW_QUALITY_REVIEW_CONTEXT.md) | Greptile/Bugbot planning-doc wiring; RQ-RC-1 |
