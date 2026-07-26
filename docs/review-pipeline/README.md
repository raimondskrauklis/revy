# Review pipeline program (Revy product)

**Active program** after SaaS base W0–W8. Builds AI-assisted code review on GitHub **inside this repo** — no fork.

**Baseline tag:** `saas-base-v1` → PR #7 (`dacfc5b`). SaaS shell frozen at that tag; review work is additive on `main`.

**Prerequisite:** scaffold P0–P5 + SaaS base W0–W8 on `main`.

**Folder layout** (same discipline as [docs/saas-base](../saas-base/README.md)):

```text
docs/review-pipeline/
  README.md                          ← this index
  REVIEW_PIPELINE_FINDINGS.md        ← baseline first (always)
  REVIEW_PIPELINE_GENERAL_PLAN.md    ← index → per-phase general plans
  REVIEW_PIPELINE_R*_…_GENERAL_PLAN.md
  REVIEW_PIPELINE_PROGRAM.md         ← branching, tags, releases
  GITHUB_WEBHOOK_DEV.md              ← local ops
  waves/
    README.md                        ← execution table
    REVIEW_PIPELINE_R*_EXECUTION.md  ← LOOP files only
```

---

## Planning (order matters)

| Step | Doc | Purpose |
|------|-----|---------|
| 1 | [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) | Baseline, catalog, locked decisions, GitHub App ops pointers |
| 2 | `REVIEW_PIPELINE_R*_GENERAL_PLAN.md` | Per-phase goals (or [R3–R7 outline](./REVIEW_PIPELINE_R3_R7_GENERAL_PLAN.md) until split) |
| 3 | [waves/REVIEW_PIPELINE_R*_EXECUTION.md](./waves/) | Subphases + phase gate — **after** general plan peer-review |
| — | [REVIEW_PIPELINE_PROGRAM.md](./REVIEW_PIPELINE_PROGRAM.md) | Branching, milestone tags, releases |
| — | [REVIEW_PIPELINE_GENERAL_PLAN.md](./REVIEW_PIPELINE_GENERAL_PLAN.md) | Index of all phase general plans |

**GitHub App (external):** [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) · [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) · [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md)

**Product authority (contributors):** `internal-docs/product/revy/docs/architecture.md`, `WEBHOOKS.md`, [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md).

---

## Phases (general plans)

| Phase | General plan | Focus |
|-------|--------------|-------|
| R0 | [R0 webhooks](./REVIEW_PIPELINE_R0_WEBHOOKS_GENERAL_PLAN.md) | Webhook ingest, HMAC, `github_events` |
| R1 | [R1 repo sync](./REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md) | `github_repositories`, `repo_sync` |
| R2 | [R2 PR ingestion](./REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md) | PR + revisions |
| R3–R7 | [R3–R7 outline](./REVIEW_PIPELINE_R3_R7_GENERAL_PLAN.md) | Index → review → publish → UI |

## Program status

| Phase | Execution | Status |
|-------|-----------|--------|
| **P4** | [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md) | **shipped** |
| **R0** | [waves/R0](./waves/REVIEW_PIPELINE_R0_EXECUTION.md) | shipped (`review-r0-v1`) |
| **R1** | [waves/R1](./waves/REVIEW_PIPELINE_R1_EXECUTION.md) | shipped (`review-r1-v1`) |
| **R2** | — | findings + general plan ready → execution next |
| **R3–R7** | — | outline only |

Full execution table: [waves/README.md](./waves/README.md).

---

## Locked principles

| Topic | Decision |
|-------|----------|
| **Repo** | Single repo — `main` + feature branches; **no fork** |
| **Planning** | Findings → general plan → execution (R0/R1 retro-documented) |
| **Releases** | Tags `review-r*-v*` on `main` → GitHub Release (GitHub App code included even when env not configured) |
| **Tenancy** | Workspace-scoped; installations → `workspaces.id` |
| **GitHub optional** | SaaS shell runs without App; review features need webhook secret / App creds when used |
| **Migrations** | Hand-written Alembic only |
| **Tests** | `backend/tests/unit/` + Vitest |
| **i18n** | EN + LV for user-facing strings |

---

## Next

1. Lock R2 open questions in [findings](./REVIEW_PIPELINE_FINDINGS.md) § R2.
2. `create-execution-plan` → [waves/REVIEW_PIPELINE_R2_EXECUTION.md](./waves/REVIEW_PIPELINE_R2_EXECUTION.md).
3. Branch `feat/review-r2-pr-ingestion` → `phase-execution`.
