# Review pipeline — execution index

Linear **phase-execution** order.

**Prerequisites (no shortcuts):**

1. [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md) — baseline-ready
2. Per-phase [general plan](../REVIEW_PIPELINE_GENERAL_PLAN.md) — **manual peer-review** (separate agent; `architecture-peer-review` skill)
3. This execution file — **manual peer-review** (separate agent; `execution-peer-review` skill) before `phase-execution`

**Peer review is not automated:** the agent that writes the plan does not self-certify. When files are ready, the **human** runs another LLM session with the peer-review skill.

**Product context:** [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) — defer/future map (Greptile-category reference).

**Authority:** [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md), [GITHUB_APP_SETUP.md](../../utils/GITHUB_APP_SETUP.md), [GITHUB_APP_TARGET_CONFIG.md](../../utils/GITHUB_APP_TARGET_CONFIG.md).

## Polish wave (post R6–R7)

Baseline: [REVIEW_PIPELINE_POLISH_FINDINGS.md](../REVIEW_PIPELINE_POLISH_FINDINGS.md) · General plan: [REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md](../REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md).

**Branch:** `feat/review-polish` · **LOOP order:** P0 → P1 → P2 (P1 ∥ P2 allowed after P0 migration lands; commit order P0 → P1 → P2).

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| P0 — Schema + enums | `suggestion`, `judge_status` columns | [REVIEW_PIPELINE_POLISH_P0_EXECUTION.md](./REVIEW_PIPELINE_POLISH_P0_EXECUTION.md) | done |
| P1 — Suggestion pipeline | R6-Q3 GitHub suggestion blocks | [REVIEW_PIPELINE_POLISH_P1_EXECUTION.md](./REVIEW_PIPELINE_POLISH_P1_EXECUTION.md) | done |
| P2 — Judge skipped badge | Reviewer UI + reconcile persist | [REVIEW_PIPELINE_POLISH_P2_EXECUTION.md](./REVIEW_PIPELINE_POLISH_P2_EXECUTION.md) | done |

---

## Program phases (R0–R8)

| Phase | General plan | Execution | Status |
|-------|--------------|-----------|--------|
| R0 — GitHub webhooks | [R0](../REVIEW_PIPELINE_R0_WEBHOOKS_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R0_EXECUTION.md](./REVIEW_PIPELINE_R0_EXECUTION.md) | done (`review-r0-v1`) |
| R1 — Repository sync | [R1](../REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R1_EXECUTION.md](./REVIEW_PIPELINE_R1_EXECUTION.md) | done (`review-r1-v1`) |
| R2 — PR ingestion | [R2](../REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R2_EXECUTION.md](./REVIEW_PIPELINE_R2_EXECUTION.md) | done (`review-r2-v1`) |
| R3 — Indexing | [R3](../REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R3_EXECUTION.md](./REVIEW_PIPELINE_R3_EXECUTION.md) | done (`review-r3-v1`) |
| R4 — Review run | [R4](../REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R4_EXECUTION.md](./REVIEW_PIPELINE_R4_EXECUTION.md) | done — `main` ([#24](https://github.com/raimondskrauklis/revy/pull/24)) |
| R5 — Reconcile + judge | [R5](../REVIEW_PIPELINE_R5_RECONCILE_JUDGE_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R5_EXECUTION.md](./REVIEW_PIPELINE_R5_EXECUTION.md) | done — `main` ([#29](https://github.com/raimondskrauklis/revy/pull/29)) |
| R6 — GitHub publish | [R6](../REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R6_EXECUTION.md](./REVIEW_PIPELINE_R6_EXECUTION.md) | done — `main` ([#29](https://github.com/raimondskrauklis/revy/pull/29)) |
| R7 — Reviewer UI | [R7](../REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R7_EXECUTION.md](./REVIEW_PIPELINE_R7_EXECUTION.md) | done — `main` ([#29](https://github.com/raimondskrauklis/revy/pull/29)) |
| R8 — Automation | [R8](../REVIEW_PIPELINE_R8_AUTOMATION_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R8_EXECUTION.md](./REVIEW_PIPELINE_R8_EXECUTION.md) | done — `main` (#31) |

**Program status:** R0–R8 on `main`; R8 merged (#31).

---

## Review quality (post-R8)

Baseline: [REVIEW_QUALITY_FINDINGS.md](../review-quality/REVIEW_QUALITY_FINDINGS.md) · Peer review: [REVIEW_QUALITY_PEER_REVIEW.md](../review-quality/REVIEW_QUALITY_PEER_REVIEW.md) · General plans: [index](../review-quality/REVIEW_QUALITY_GENERAL_PLAN.md).

**Branch:** merged to `main` (PR [#50](https://github.com/raimondskrauklis/revy/pull/50)) · **LOOP:** RQ0 → … → RQ8 ✓ · **Active:** RQ9 on `docs/agent-work`

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| **Review quality** | Diff-first + trace + Greptile publish + evidence + metrics | [REVIEW_QUALITY_EXECUTION.md](./REVIEW_QUALITY_EXECUTION.md) | **merged** — RQ9 hardening before human gate |
| **RQ9 — Hardening** | G10 neutral finalize, TX tests, agent doc wiring | [REVIEW_QUALITY_EXECUTION.md](./REVIEW_QUALITY_EXECUTION.md) § RQ9 | **active** — `docs/agent-work` |

**Tag after human gate:** `review-quality-v1`

**Post-v1 (same program folder):**

| Track | Focus | When |
|-------|--------|------|
| **RQ-STRUCT-1** | Cross-file grep/import bridge | After tag — [structural context](../review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| **RQ-RC-1** | Greptile/Bugbot planning-doc improvements | After tag — [review context](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) |
| **RQ9** | Post-merge hardening (G10 parking, TX tests) | **active** — [R9 general plan](../review-quality/REVIEW_QUALITY_R9_HARDENING_GENERAL_PLAN.md) |

---

## GitHub surface (post review-quality)

Baseline: [post-review-quality/](../post-review-quality/README.md) · **LOOP:** P0 → P1 → P2 → P3 → P4 · **PR:** [#52](https://github.com/raimondskrauklis/revy/pull/52) (ready to merge)

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| P0 — Worker + dogfood | Publish path + first row | [GITHUB_SURFACE_P0_EXECUTION.md](../post-review-quality/GITHUB_SURFACE_P0_EXECUTION.md) | **merged** (#52) |
| P1 — L2 triage | Issue comment + G3 | [GITHUB_SURFACE_P1_EXECUTION.md](../post-review-quality/GITHUB_SURFACE_P1_EXECUTION.md) | **merged** (#52) |
| P2 — L1 presence | G10 lifecycle | [GITHUB_SURFACE_P2_EXECUTION.md](../post-review-quality/GITHUB_SURFACE_P2_EXECUTION.md) | **merged** (#52) |
| P3 — L3 inline | Warning threads | [GITHUB_SURFACE_P3_EXECUTION.md](../post-review-quality/GITHUB_SURFACE_P3_EXECUTION.md) | **merged** (#52) |
| P4 — Doc sync | PRODUCT_PATTERNS | [GITHUB_SURFACE_P4_EXECUTION.md](../post-review-quality/GITHUB_SURFACE_P4_EXECUTION.md) | done |

**Next:** [POST_REVIEW_QUALITY_FOLLOWUPS.md](../post-review-quality/POST_REVIEW_QUALITY_FOLLOWUPS.md) · Index: [GITHUB_SURFACE_EXECUTION.md](../post-review-quality/GITHUB_SURFACE_EXECUTION.md)
