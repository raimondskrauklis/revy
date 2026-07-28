# Review quality program (post-R8)

**Status:** RQ0–RQ8 **merged to `main`** (PR [#50](https://github.com/raimondskrauklis/revy/pull/50)). **RQ9** hardening active on `docs/agent-work`. **Tag:** `review-quality-v1` after human gate.

Post-R8 program: **diff-first review**, **pipeline explainability**, Greptile-shaped **GitHub publish**, incremental index (C1), evidence + grounding, resolution metrics. R0–R8 = core pipeline.

**Prerequisite:** R0–R8 on `main` ✓

---

## Docs (order)

| Step | Doc | Purpose |
|------|-----|---------|
| 1 | [REVIEW_QUALITY_FINDINGS.md](./REVIEW_QUALITY_FINDINGS.md) | Baseline + Q-registry — **start here** |
| 2 | [REVIEW_QUALITY_GENERAL_PLAN.md](./REVIEW_QUALITY_GENERAL_PLAN.md) | Index → per-slice general plans |
| 3 | [R1](./REVIEW_QUALITY_R1_DIFF_AND_TRACE_GENERAL_PLAN.md) · [R2](./REVIEW_QUALITY_R2_INCREMENTAL_INDEX_GENERAL_PLAN.md) · [R3](./REVIEW_QUALITY_R3_GITHUB_PUBLISH_GENERAL_PLAN.md) · [R4](./REVIEW_QUALITY_R4_EVIDENCE_JUDGE_GENERAL_PLAN.md) · [R5](./REVIEW_QUALITY_R5_RESOLUTION_METRICS_GENERAL_PLAN.md) | Slice general plans |
| 4 | [REVIEW_QUALITY_EXECUTION.md](../waves/REVIEW_QUALITY_EXECUTION.md) | RQ0–RQ9 execution (RQ0–RQ8 shipped; RQ9 active) |
| — | [REVIEW_QUALITY_R9_HARDENING_GENERAL_PLAN.md](./REVIEW_QUALITY_R9_HARDENING_GENERAL_PLAN.md) | Post-merge hardening slice |
| — | [REVIEW_QUALITY_PEER_REVIEW.md](./REVIEW_QUALITY_PEER_REVIEW.md) | Architecture peer review + pre-execution locks |
| — | [agents/](../agents/README.md) | **How we build** — LOOP, gates, prompts |
| — | [CURSOR_AGENT_WORKFLOW.md](../../utils/CURSOR_AGENT_WORKFLOW.md) | **Quick ref** — human / master / Bugbot |
| — | [REVIEW_QUALITY_DOGFOOD_PR50.md](./REVIEW_QUALITY_DOGFOOD_PR50.md) | **Evidence** — PR #50 Greptile vs Revy |
| — | [REVIEW_QUALITY_REVIEW_CONTEXT.md](./REVIEW_QUALITY_REVIEW_CONTEXT.md) | Bot wiring (RC0); RC1/RC2/RC5 → [RCX](../review-engineering-context/) |
| — | [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) | Post-v1 code graph (SC) |

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
| **RC** — Review context | Greptile/Bugbot ↔ planning docs; RQ0 v0; **RCX** for Moonshot inject + Greptile SSOT |

---

## Locked decisions (summary)

| Topic | Resolution |
|-------|------------|
| Ship | One PR, one execution file (S1–S2) — **merged** |
| Autostart profile | `standard` → `diff` until workspace profile setting (AS1) |
| Autostart bug | Staging e2e gate (AS2); fix only if gate fails |
| Diff index | Compare for list+diff; tarball for changed paths only (D13) |
| Pipeline read | `items_view` read; `admin_users` retention (O9) |
| Fingerprint | D10 in same PR |
| Fixed prose | R5 owns status; R3 reads (G9) |
| LSP / cross-file | Defer full LSP v1; north star **graph + agents** (SC8) |
| PR review context | RQ0 wires `.greptile/files.json` + `.cursor/BUGBOT.md` (RC0) |

---

## Related

| Doc | Role |
|-----|------|
| [../README.md](../README.md) | Review pipeline program index |
| [../waves/README.md](../waves/README.md) | Execution table (R0–R8 + review quality) |
| [../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) | Agent handoff — ops + human gate |
