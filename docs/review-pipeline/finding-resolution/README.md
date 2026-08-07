# Finding resolution program

**Status:** **shipped on branch** (`feat/finding-resolution`, PR [#57](https://github.com/raimondskrauklis/revy/pull/57)) — code-complete P0–P5; **staging human gate pending** ([validation memo](./FINDING_RESOLUTION_STAGING_VALIDATION.md)).

**LOOP mode (operator):** Agent implements one phase → local commit → operator pushes → validates staging → next phase.

**Migration pause:** Apply `0028` on staging before relying on resolution columns in production paths.

**Thesis:** How Revy decides a finding is **addressed**, **dismissed**, or **still open** — multi-pass closure after each push + resolution-rate metrics.

**GitHub thread collapse (GH-1v2):** Pass 1 `addressed` + publish-time resolve (Option A/B/outdated/sync) + **`filter_pr_active_groups_for_summary`** (summary block 2) + **`_close_active_groups_for_fingerprints`** (DB) — canonical spec in [github-surface-hardening §4c](../github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md#gh-1v2--collapse-triggers-shipped-post-p4).

| Doc | Purpose |
|-----|---------|
| [FINDING_RESOLUTION_FINDINGS.md](./FINDING_RESOLUTION_FINDINGS.md) | Baseline — current flow, gaps, FR-Q registry |
| [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) | **Wave C** — cohort vs hygiene (post-dogfood) |
| [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](./FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md) | **Wave C** — phased plan (C0–C4) |
| [waves/FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md](./waves/FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md) | **Wave C LOOP** — execution index |
| [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](./FINDING_RESOLUTION_TECHNICAL_FINDINGS.md) | Incident + staging DB evidence |
| [FINDING_RESOLUTION_GENERAL_PLAN.md](./FINDING_RESOLUTION_GENERAL_PLAN.md) | P0–P5 phases, locked FR-Q*, multi-pass model |
| [FINDING_RESOLUTION_STAGING_VALIDATION.md](./FINDING_RESOLUTION_STAGING_VALIDATION.md) | Staging dogfood + human sign-off checklist |
| [FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md](./FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md) | **Post–wave C** — MR-DG1 vs FR-CS4/8 implement/defer |
| [FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md](./FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md) | **Post–wave C** — M0 + wave D phases |
| [FINDING_RESOLUTION_POST_WAVE_C_D1_FINDINGS.md](./FINDING_RESOLUTION_POST_WAVE_C_D1_FINDINGS.md) | **D1** — FR-CS4 staging dogfood baseline |
| [FINDING_RESOLUTION_POST_WAVE_C_D1_GENERAL_PLAN.md](./FINDING_RESOLUTION_POST_WAVE_C_D1_GENERAL_PLAN.md) | **D1** — dogfood phases D1.0–D1.3 |
| [waves/FINDING_RESOLUTION_POST_WAVE_C_EXECUTION.md](./waves/FINDING_RESOLUTION_POST_WAVE_C_EXECUTION.md) | **Post–wave C LOOP** — execution index |

## Execution (LOOP order)

| Phase | Focus | File | Commit | Status |
|-------|--------|------|--------|--------|
| P0 | Closure model, migration `0028`, compare helper | [P0](./waves/FINDING_RESOLUTION_P0_EXECUTION.md) | `76e8784` | done |
| P1 | Pass 1 stamp + Pass 2 reconcile closure | [P1](./waves/FINDING_RESOLUTION_P1_EXECUTION.md) | `c0522ec` / `97a7e01` | done |
| P2 | Pass 3 verification judge (5/run) | [P2](./waves/FINDING_RESOLUTION_P2_EXECUTION.md) | `c0522ec` | done |
| P3 | FR-Q12 metrics, G9, API fields | [P3](./waves/FINDING_RESOLUTION_P3_EXECUTION.md) | `73401aa` | done |
| P4 | Human dismiss, summary parity, RG-6 | [P4](./waves/FINDING_RESOLUTION_P4_EXECUTION.md) | `8b453aa` | done |
| P5 | Staging validation + doc sync | [P5](./waves/FINDING_RESOLUTION_P5_EXECUTION.md) | (P5 commit) | done (docs) |

**Related shipped programs:** R5 reconcile + judge · RQ6 resolution metrics · github-surface-hardening · generation lifecycle · judge input quality.

**Next wave:** [judge-json-contract](../judge-json-contract/README.md) after merge to `main`.

**Post-PSA dogfood (2026-07-29):** [finding-resolution-dogfood](../finding-resolution-dogfood/README.md) — FR-DG1/FR-DG2 **closed PASS**; wave C shipped ([#68](https://github.com/raimondskrauklis/revy/pull/68) + [#69](https://github.com/raimondskrauklis/revy/pull/69) C3).

**Cross-repo dogfood (2026-07-31):** [revy-review-dogfood](../revy-review-dogfood/README.md) — **RR-W1 complete** · TenderPro #130 symptoms · validation [Revy #80](https://github.com/raimondskrauklis/revy/pull/80) · shipped `deda3c9`.

## Wave C execution (LOOP)

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| C0 | SSOT + index | [C0](./waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C0_EXECUTION.md) | done (`c7c84f1`) |
| C1 | HEAD hygiene + Pass 2 | [C1](./waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C1_EXECUTION.md) | done (`d4666aa`) |
| C2 | Manifest + G9 | [C2](./waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C2_EXECUTION.md) | done (`d4666aa`) |
| C3 | Staging Track C | [C3](./waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C3_EXECUTION.md) | done (`bdb25a4` / [#69](https://github.com/raimondskrauklis/revy/pull/69)) |
| C4 | Doc sync | [C4](./waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C4_EXECUTION.md) | done |

## Revy PR review — operator notes (2026-07-31)

Cross-repo dogfood (TenderPro #130 symptoms; validation on [Revy #80](https://github.com/raimondskrauklis/revy/pull/80)) — full gap catalog: [revy-review-dogfood](../revy-review-dogfood/REVY_REVIEW_DOGFOOD_FINDINGS.md) (**RR-W1** complete).

| Observation | Notes |
|-------------|--------|
| **Signal vs Bugbot** | Revy caught real adapter bugs on Revy-repo PRs; on TenderPro, high **false-positive** rate on already-fixed HEAD code — R4 HEAD suppression shipped on `deda3c9`. |
| **Resolution UX** | **Fixed on revy venue** — DB closure SSOT; GitHub threads collapse after App **Contents: Write** (RR-DG12). |
| **How to close the loop** | Trust DB `resolution_status` + `--rr-v-gate`; manually resolve only when permission drift suspected. |
| **Ingestion** | R1 idempotency shipped — RR-V1 PASS on #80 (1 row per `head_sha`). |

**Takeaway:** Finding-resolution mechanisms shipped; **RR-W1 cross-repo operator gate** complete — ingest, publish hygiene, HEAD truth, staging validation script.
