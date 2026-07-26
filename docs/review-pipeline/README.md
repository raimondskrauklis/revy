# Review pipeline program (Revy product)

**Active program** after SaaS base W0–W8. Builds AI-assisted code review on GitHub **inside this repo** — no fork.

**Baseline tag:** `saas-base-v1` → merge commit of PR #7 (`dacfc5b`). SaaS shell, settings, billing, platform admin, lifecycle, impersonation are **frozen at that tag** for reference.

**Prerequisite:** scaffold P0–P5 + SaaS base W0–W8 on `main`.

---

## Planning

| Doc | Purpose |
|-----|---------|
| [REVIEW_PIPELINE_PROGRAM.md](./REVIEW_PIPELINE_PROGRAM.md) | Strategy, branching, phased roadmap R0–R7 |
| [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) | Baseline inventory, decisions, gaps |
| [REVIEW_PIPELINE_GENERAL_PLAN.md](./REVIEW_PIPELINE_GENERAL_PLAN.md) | Phase goals (R0–R7) |
| [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md) | Shipped P4: `github_installations` |
| [SAAS_BASE_FINDINGS.md](../saas-base/SAAS_BASE_FINDINGS.md) | SaaS base complete — out of scope for R* |

**Full product authority (contributors):** `internal-docs/product/revy/docs/architecture.md`, `PLATFORM_CONTEXT.md`, `deploy/docs/implementation.revy.md`.

**Execution:** per-phase `REVIEW_PIPELINE_R*_EXECUTION.md` files under `waves/` — created after findings + general plan (same pattern as SaaS base).

---

## Program status

| Phase | Focus | Status |
|-------|--------|--------|
| **P4** | `github_installation` list + dev register | **shipped** |
| **R0** | GitHub webhooks + event ingestion | shipped (`review-r0-v1` → `754c88c`) |
| **R1** | Repository / branch metadata sync | shipped (`review-r1-v1` → `fd29fd5`) |
| **R2** | Pull request ingestion + revisions | not started |
| **R3** | Indexing (chunks, embeddings, pgvector) | not started |
| **R4** | Review run (LLM stages) | not started |
| **R5** | Reconciliation + judge | not started |
| **R6** | GitHub publish (checks, review comments) | not started |
| **R7** | Findings + reviewer UI | not started |

---

## Locked principles

| Topic | Decision |
|-------|----------|
| **Repo** | Single repo — `main` + feature branches; **no GitHub fork** for Revy product work |
| **Base** | SaaS shell is additive foundation; tag `saas-base-v1` for snapshot; bugfixes on `main` |
| **Tenancy** | Workspace-scoped; installations already linked to `workspaces.id` |
| **Workers** | Celery queue map wired in `celery_app.py`; task modules stubbed until R* |
| **Migrations** | Hand-written Alembic only |
| **Tests** | `backend/tests/unit/` + Vitest; no new `tests/api/` |
| **i18n** | EN + LV for all user-facing strings |

---

## Next

1. Plan **R2** (PR ingestion) — `REVIEW_PIPELINE_R2_EXECUTION.md`.
2. Branch `feat/review-r2-pr-ingestion` when R2 execution is ready.
