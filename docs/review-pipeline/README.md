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
  REVIEW_PIPELINE_GREPTILE_PR26_EMAIL.md   ← archived Greptile PR #26 email (triage reference)
  REVIEW_PIPELINE_PRODUCT_PATTERNS.md      ← Greptile-style patterns → Revy phases (defer/future map)
  code-review-arch_perplexity_searcj_advice_only.md  ← external architecture notes (advice only)
  GITHUB_WEBHOOK_DEV.md                    ← local ops
  waves/
    README.md                              ← execution table only
    REVIEW_PIPELINE_R*_EXECUTION.md        ← ③ after general plan peer-review
```

---

## Getting back on track (program discipline)

R0 and R1 **shipped before** the full planning ladder was enforced. Recovery steps taken / required:

| Step | R0 / R1 (shipped) | R2+ (forward) |
|------|---------------------|---------------|
| **Findings** | Retroactive update in [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) | Must be baseline-ready **before** execution |
| **General plan** | Retroactive — [R0](./REVIEW_PIPELINE_R0_WEBHOOKS_GENERAL_PLAN.md), [R1](./REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md) | One file per phase — **all R0–R7 now exist** |
| **Execution** | [R0](./waves/REVIEW_PIPELINE_R0_EXECUTION.md), [R1](./waves/REVIEW_PIPELINE_R1_EXECUTION.md) shipped | Create after general plan; **manual peer-review** (separate agent) before `phase-execution` |
| **Code** | R0–R3 on `main` (`review-r0-v1` … `review-r3-v1`); R4–R7 on PR stack [#24](https://github.com/raimondskrauklis/revy/pull/24)–[#27](https://github.com/raimondskrauklis/revy/pull/27) | tag `review-r4-v1` … `review-r7-v1` after merge |
| **GitHub App** | [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) · [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) | Configure per phase map in target config |

**No corners cut from R2 onward:** findings locked → general plan → execution plan → peer-review → implement → phase gate → tag.

---

## Planning (order matters)

| Step | Doc | Purpose |
|------|-----|---------|
| 1 | [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) | Baseline, catalog, locked decisions |
| 2 | `REVIEW_PIPELINE_R*_GENERAL_PLAN.md` | Per-phase goals — [index](./REVIEW_PIPELINE_GENERAL_PLAN.md) |
| 3 | [waves/REVIEW_PIPELINE_R*_EXECUTION.md](./waves/) | Subphases + phase gate |
| — | [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Industry patterns (Greptile reference) → Revy roadmap; nothing dropped |
| — | [REVIEW_PIPELINE_PROGRAM.md](./REVIEW_PIPELINE_PROGRAM.md) | Branching, milestone tags |

---

## Phases (general plans) — all R0–R7

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

## Program status

| Phase | Execution | Status |
|-------|-----------|--------|
| **P4** | [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md) | shipped |
| **R0** | [waves/R0](./waves/REVIEW_PIPELINE_R0_EXECUTION.md) | shipped (`review-r0-v1`) |
| **R1** | [waves/R1](./waves/REVIEW_PIPELINE_R1_EXECUTION.md) | shipped (`review-r1-v1`) |
| **R2** | [waves/R2](./waves/REVIEW_PIPELINE_R2_EXECUTION.md) | shipped (`review-r2-v1`) |
| **R3** | [waves/R3](./waves/REVIEW_PIPELINE_R3_EXECUTION.md) | shipped (`review-r3-v1`) |
| **R4** | [waves/R4](./waves/REVIEW_PIPELINE_R4_EXECUTION.md) | implemented — PR [#24](https://github.com/raimondskrauklis/revy/pull/24); tag `review-r4-v1` after merge |
| **R5** | [waves/R5](./waves/REVIEW_PIPELINE_R5_EXECUTION.md) | implemented — PR [#25](https://github.com/raimondskrauklis/revy/pull/25) (base #24) |
| **R6** | [waves/R6](./waves/REVIEW_PIPELINE_R6_EXECUTION.md) | implemented — PR [#26](https://github.com/raimondskrauklis/revy/pull/26) (base #25) |
| **R7** | [waves/R7](./waves/REVIEW_PIPELINE_R7_EXECUTION.md) | implemented — PR [#27](https://github.com/raimondskrauklis/revy/pull/27) (base #26) |

[waves/README.md](./waves/README.md) — full execution table. **Docs sync:** PR [#23](https://github.com/raimondskrauklis/revy/pull/23) (`chore/review-pipeline-docs-sync`).

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

1. **Merge PR stack** — [#23](https://github.com/raimondskrauklis/revy/pull/23) (docs) → [#24](https://github.com/raimondskrauklis/revy/pull/24) → [#25](https://github.com/raimondskrauklis/revy/pull/25) → [#26](https://github.com/raimondskrauklis/revy/pull/26) → [#27](https://github.com/raimondskrauklis/revy/pull/27); rebase stack onto `main` after each merge.
2. **Ops** — `alembic upgrade head` (migrations `0014`–`0016`); set `MOONSHOT_API_KEY`, `VOYAGE_API_KEY`, optional `ANTHROPIC_API_KEY`, `REVY_BOT_LOGIN`; worker consumes full queue list (see [PROGRAM](./REVIEW_PIPELINE_PROGRAM.md) §5).
3. **Tags** — `review-r4-v1` … `review-r7-v1` on `main` after each phase merge.
4. **Post-R7** — R8 [automation](./REVIEW_PIPELINE_R8_AUTOMATION_GENERAL_PLAN.md) (`Q11` + R8-Q1–R8-Q7); execution peer-reviewed; `phase-execution` on `feat/review-r8-automation` after dogfood.
