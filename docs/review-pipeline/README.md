# Review pipeline program (Revy product)

**Active program** after SaaS base W0–W8. Builds AI-assisted code review on GitHub **inside this repo** — no fork.

**Baseline tag:** `saas-base-v1` → PR #7 (`dacfc5b`). SaaS shell frozen at that tag; review work is additive on `main`.

**Prerequisite:** scaffold P0–P5 + SaaS base W0–W8 on `main`.

**Folder layout** (mirrors [docs/saas-base](../saas-base/README.md)):

```text
docs/review-pipeline/
  README.md                              ← program index (this file)
  REVIEW_PIPELINE_FINDINGS.md            ← ① baseline first — always
  REVIEW_PIPELINE_GENERAL_PLAN.md        ← index → per-phase general plans
  REVIEW_PIPELINE_R0_…_GENERAL_PLAN.md   ← ② one file per phase (R0–R7)
  …
  REVIEW_PIPELINE_PROGRAM.md               ← branching, tags, releases
  REVIEW_PIPELINE_RECOVERY_CHECKLIST.md    ← agent handoff + active tracks
  REVIEW_PIPELINE_MERGE_CHECKLIST.md       ← babysit + merge gates (R4–R7 stack)
  REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md ← Greptile babysit + industry patterns → product backlog
  agents/                                  ← living: Cursor LOOP, Bugbot, prompts (update each RQ)
    README.md
    ORCHESTRATION.md
    PROMPTS.md
  REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md ← 2026-07-27 staging e2e smoke + hotfix log
  review-quality/                          ← post-R8: diff-first, trace, GitHub publish
    README.md                              ← program index
    REVIEW_QUALITY_FINDINGS.md             ← ① baseline
    REVIEW_QUALITY_PEER_REVIEW.md          ← architecture peer review + pre-execution locks
    REVIEW_QUALITY_STRUCTURAL_CONTEXT.md   ← LSP defer; cross-file roadmap (SC8)
  post-review-quality/                     ← v1.1+ gaps from PR #51 dogfood
    README.md
    POST_REVIEW_QUALITY_FINDINGS.md        ← ① next-wave baseline
  review-generation-lifecycle/             ← snapshot semantics: HEAD-gate, supersede, no spill
    README.md
    REVIEW_GENERATION_LIFECYCLE_FINDINGS.md  ← ① baseline (PR #53 dogfood)
  judge/                                   ← R5 judge input quality (Moonshot vs judge context)
    README.md
    JUDGE_INPUT_INVESTIGATION_FINDINGS.md
    JUDGE_INPUT_QUALITY_GENERAL_PLAN.md
    waves/
      JUDGE_INPUT_QUALITY_EXECUTION.md       ← LOOP index
      JUDGE_INPUT_QUALITY_P0_EXECUTION.md … P5
  finding-resolution/                      ← addressed / dismissed / still open + resolution rate
    README.md
    FINDING_RESOLUTION_FINDINGS.md
    FINDING_RESOLUTION_GENERAL_PLAN.md
    FINDING_RESOLUTION_STAGING_VALIDATION.md
    waves/
      FINDING_RESOLUTION_EXECUTION.md
      FINDING_RESOLUTION_P0_EXECUTION.md … P5
  REVIEW_PIPELINE_GREPTILE_PR26_EMAIL.md   ← archived Greptile PR #26 email (triage reference)
  REVIEW_PIPELINE_PRODUCT_PATTERNS.md      ← Greptile-style patterns → Revy phases (defer/future map)
  code-review-arch_perplexity_searcj_advice_only.md  ← external architecture notes (advice only)
  GITHUB_WEBHOOK_DEV.md                    ← local ops
    waves/
    README.md                              ← execution table only
    REVIEW_PIPELINE_R*_EXECUTION.md        ← R0–R8
    REVIEW_QUALITY_EXECUTION.md            ← review-quality RQ0–RQ8
```

---

## Getting back on track (program discipline)

R0 and R1 **shipped before** the full planning ladder was enforced. Recovery steps taken / required:

| Step | R0 / R1 (shipped) | R2+ (forward) |
|------|---------------------|---------------|
| **Findings** | Retroactive update in [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) | Must be baseline-ready **before** execution |
| **General plan** | Retroactive — [R0](./REVIEW_PIPELINE_R0_WEBHOOKS_GENERAL_PLAN.md), [R1](./REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md) | One file per phase — **all R0–R7 now exist** |
| **Execution** | [R0](./waves/REVIEW_PIPELINE_R0_EXECUTION.md), [R1](./waves/REVIEW_PIPELINE_R1_EXECUTION.md) shipped | Create after general plan; **manual peer-review** (separate agent) before `phase-execution` |
| **Code** | R0–R8 + review-quality on `main` | Findings → general plan → execution → code |
| **GitHub App** | [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) · [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) | Configure per phase map in target config |

**No corners cut from R2 onward:** findings locked → general plan → execution plan → peer-review → implement → phase gate → tag.

---

## Planning (order matters)

| Step | Doc | Purpose |
|------|-----|---------|
| 1 | [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) | Baseline, catalog, locked decisions |
| 2 | `REVIEW_PIPELINE_R*_GENERAL_PLAN.md` | Per-phase goals — [index](./REVIEW_PIPELINE_GENERAL_PLAN.md) |
| 3 | [waves/REVIEW_PIPELINE_R*_EXECUTION.md](./waves/) | Subphases + phase gate |
| — | [REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md](./REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md) | 2026-07-27 staging e2e smoke + hotfix chronology |
| — | [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Industry patterns (Greptile reference) → Revy roadmap; nothing dropped |
| — | [REVIEW_PIPELINE_PROGRAM.md](./REVIEW_PIPELINE_PROGRAM.md) | Branching, milestone tags |

---

## Phases (general plans) — R0–R8

| Phase | General plan | Focus |
|-------|--------------|-------|
| R0 | [R0 webhooks](./REVIEW_PIPELINE_R0_WEBHOOKS_GENERAL_PLAN.md) | Webhook ingest, HMAC, `github_events` |
| R1 | [R1 repo sync](./REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md) | `github_repositories`, `repo_sync` |
| R2 | [R2 PR ingestion](./REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md) | PR + revisions |
| R3 | [R3 indexing](./REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md) | Chunks, embeddings, pgvector |
| R4 | [R4 review run](./REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md) | LLM pipeline, findings |
| R5 | [R5 reconcile + judge](./REVIEW_PIPELINE_R5_RECONCILE_JUDGE_GENERAL_PLAN.md) | Fingerprints, escalation |
| R6 | [R6 GitHub publish](./REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md) | Checks, PR comments |
| R7 | [R7 reviewer UI](./REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md) | `features/reviewer/` |
| R8 | [R8 automation](./REVIEW_PIPELINE_R8_AUTOMATION_GENERAL_PLAN.md) | Autostart, `@revy review`, workspace toggle |
| Review quality | [review-quality/](./review-quality/README.md) | R1–R5 general plans; [index](./review-quality/REVIEW_QUALITY_GENERAL_PLAN.md) |

## Program status

| Phase | Execution | Status |
|-------|-----------|--------|
| **P4** | [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md) | shipped |
| **R0** | [waves/R0](./waves/REVIEW_PIPELINE_R0_EXECUTION.md) | shipped (`review-r0-v1`) |
| **R1** | [waves/R1](./waves/REVIEW_PIPELINE_R1_EXECUTION.md) | shipped (`review-r1-v1`) |
| **R2** | [waves/R2](./waves/REVIEW_PIPELINE_R2_EXECUTION.md) | shipped (`review-r2-v1`) |
| **R3** | [waves/R3](./waves/REVIEW_PIPELINE_R3_EXECUTION.md) | shipped (`review-r3-v1`) |
| **R4** | [waves/R4](./waves/REVIEW_PIPELINE_R4_EXECUTION.md) | shipped on `main` ([#24](https://github.com/raimondskrauklis/revy/pull/24)) |
| **R5** | [waves/R5](./waves/REVIEW_PIPELINE_R5_EXECUTION.md) | shipped on `main` ([#29](https://github.com/raimondskrauklis/revy/pull/29)) |
| **R6** | [waves/R6](./waves/REVIEW_PIPELINE_R6_EXECUTION.md) | shipped on `main` ([#29](https://github.com/raimondskrauklis/revy/pull/29)) |
| **R7** | [waves/R7](./waves/REVIEW_PIPELINE_R7_EXECUTION.md) | shipped on `main` ([#29](https://github.com/raimondskrauklis/revy/pull/29)) |
| **R8** | [waves/R8](./waves/REVIEW_PIPELINE_R8_EXECUTION.md) | shipped on `main` ([#31](https://github.com/raimondskrauklis/revy/pull/31)) |
| **Review quality** | [review-quality/](./review-quality/README.md) | shipped on `main` ([#50](https://github.com/raimondskrauklis/revy/pull/50)) — tag `review-quality-v1` after human gate |

[waves/README.md](./waves/README.md) — full execution table.

---

## Locked principles

| Topic | Decision |
|-------|----------|
| **Planning** | Findings → general plan → execution → code (R0/R1 retro-documented) |
| **Repo** | Single repo — `main` + feature branches |
| **Releases** | Tags `review-r*-v*` on `main`; GitHub App code included even when env unset |
| **GitHub App** | External setup via `docs/utils/` runbooks |
| **Tenancy** | Workspace-scoped on all domain rows |
| **Migrations** | Hand-written Alembic only |
| **Tests** | `backend/tests/unit/` + Vitest |
| **i18n** | EN + LV for user-facing strings |

---

## Next (strict order)

1. **Human gate** — staging `0026` + AS2 e2e — [REVIEW_QUALITY_EXECUTION.md § RQ8](./waves/REVIEW_QUALITY_EXECUTION.md); then tag `review-quality-v1`.
2. **Ops** — Track F in [recovery checklist](./REVIEW_PIPELINE_RECOVERY_CHECKLIST.md): migrations through `0026`; env keys; worker `-Q` + Celery beat (O8 purge).
3. **Post-v1** — RQ-STRUCT-1 / RQ-RC-1 when ready — [review-quality/README.md](./review-quality/README.md).
