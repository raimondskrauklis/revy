# Review pipeline — findings

Baseline for Revy **AI code review on GitHub** after SaaS base W0–W8 + P4 installations. **No execution steps.**

**Status:** baseline-ready (2026-07-26). **Tag:** `saas-base-v1` → PR #7; infra fix in `saas-base-v1.1` (Alembic AUTOCOMMIT).

**Program:** [README.md](./README.md) · **Authority (full):** `internal-docs/product/revy/docs/architecture.md`, `WEBHOOKS.md`, `REVY_PRODUCT_SLICE.md`.

---

## Build principles

- **Additive** on SaaS shell — no fork; workspace tenancy on all domain rows.
- **GitHub App** webhooks + API; installation token cache; Celery queues per `REVY_PRODUCT_SLICE.md`.
- **Hand-written Alembic**; unit tests only (`backend/tests/unit/`).
- **EN+LV** for user-facing strings; `--app-*` tokens.
- **Never block webhook HTTP** on GitHub API — persist + enqueue.

---

## What exists vs genuinely new

| Area | Exists (verified) | New (R0–R7) |
|------|-------------------|-------------|
| **Installations** | `github_installations` table, CRUD API, `/installations` UI, plan gate `installations.create` | OAuth install flow (defer); link webhooks → rows |
| **Webhooks** | `POST /api/v1/webhooks/stripe` — raw body, idempotent (`stripe_webhook_events`) | `POST /api/v1/webhooks/github` |
| **Celery routes** | `celery_app.py` maps `github_tasks.*` → `github_events`, etc. | Task modules: `github_tasks`, `repo_tasks`, … |
| **Workers deployed** | CI: `-Q default,notifications,heavy` | v1: full Revy queue set (see § Deploy) |
| **Config** | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY_PATH`, `GITHUB_WEBHOOK_SECRET`, `REVY_BOT_LOGIN` in `config.py` + `.env.example` | App auth client, token cache |
| **ORM** | `GitHubInstallationORM` | `repository`, `pull_request`, review/findings, embeddings |
| **Frontend** | `features/installations/` | `features/reviewer/` (R7) |
| **Migrations** | `0001`–`0009` (through impersonation) | R1+ entity migrations |
| **internal-docs** | `product/revy/docs/WEBHOOKS.md`, `architecture.md` (gitignored, local) | Mirror critical ops into `docs/` when shipped |

**Trap:** `heavy_job` routed in `celery_app.py` but **not defined** in `tasks.py` — SaaS carryover; remove or stub in R0 cleanup.

---

## Catalog (phased)

| Phase | Capability | Rationale |
|-------|------------|-----------|
| **R0** | GitHub webhook ingest + HMAC + delivery dedupe + `github_events` enqueue | `WEBHOOKS.md`; unblock all downstream |
| **R1** | Repository metadata sync (`repo_sync`) | Installation-scoped repo allowlist |
| **R2** | PR ingestion + revisions | `pull_request` events |
| **R3** | Indexing (chunks, pgvector) | `vector` extension already in deploy SQL |
| **R4** | LLM review stages | Core product value |
| **R5** | Reconciliation + judge | Finding fingerprints |
| **R6** | GitHub publish (checks, comments) | `github_publish` queue |
| **R7** | Reviewer UI + dashboard hooks | Member-facing product |

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| Q1 | Same repo vs fork? | **locked** | Same repo; `saas-base-v1` tag |
| Q2 | Webhook path | **locked** | `POST /api/v1/webhooks/github` per `WEBHOOKS.md` |
| Q3 | Delivery dedupe store | **locked** | DB table `github_webhook_deliveries` (mirror Stripe pattern); TTL via periodic cleanup or `expires_at` |
| Q4 | Handler response | **locked** | Verify → dedupe → enqueue Celery → **200**; never call GitHub API in handler |
| Q5 | R0 event scope | **locked** | `installation`, `installation_repositories`, `push` (minimal); expand in R1/R2 |
| Q6 | Worker deploy | **locked** | Document v1 queue list; CI worker update in R0 or R1 deploy subphase |
| Q7 | Plan gates on review | **defer** | After R4 — volume/LLM cost gating TBD |
| Q8 | OAuth GitHub App install UI | **defer** | Manual register (P4) until R1+ |

---

## Edge cases

| Case | Handling |
|------|----------|
| Webhook for unknown `installation_id` | Log + **200** (no retry storm); align Stripe orphan policy |
| Duplicate `X-GitHub-Delivery` | Idempotent ack from dedupe table |
| Installation `removed` / `suspended` | Update `github_installations.status` on `installation` event |
| Cross-workspace installation ID conflict | Already blocked at register (`ConflictError`) |
| Pooled vs direct DB URL for migrations | **AUTOCOMMIT** required in `alembic/env.py` (see § Infra) |

---

## Infra fix (saas-base-v1.1)

**Verified:** `backend/alembic/env.py` — async online migrations use `isolation_level="AUTOCOMMIT"` before `run_sync(do_run_migrations)`.

Without AUTOCOMMIT, asyncpg rolls back on disconnect → empty DB, no `alembic_version`, misleading success logs. Hand-written revisions in `alembic/versions/` were always correct.

---

## Parking lot

- GitHub App production registration automation
- nginx GitHub IP allowlist
- In-app OAuth install redirect
- `heavy_job` task definition or route removal
- Worker autoscaling per queue

---

## Experiment / verification

| Check | Pass |
|-------|------|
| `alembic upgrade head` on fresh DB | Tables + `alembic_version` row present |
| Manual installation register | Row in `github_installations` |
| R0: `gh webhook` / smee.io → API | **200**, delivery row, Celery task received |
| R2+: synthetic PR event | `pull_request` row created |
| R7: UI lists findings | EN+LV strings |

---

## References

| Path | Role |
|------|------|
| [REVIEW_PIPELINE_PROGRAM.md](./REVIEW_PIPELINE_PROGRAM.md) | Branching, phases |
| [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md) | P4 shipped scope |
| `backend/app/services/github_installations.py` | Installation service |
| `backend/app/api/v1/webhooks/stripe.py` | Webhook pattern |
| `backend/app/workers/celery_app.py` | Queue routes |
| `internal-docs/product/revy/docs/WEBHOOKS.md` | GitHub webhook spec |
| `internal-docs/product/revy/docs/architecture.md` | Full pipeline |
