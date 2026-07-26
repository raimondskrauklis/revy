# Review pipeline — findings

Baseline for Revy **AI code review on GitHub** after SaaS base W0–W8 + P4 installations. **No execution steps.**

**Status:** baseline-ready (2026-07-26). **Shipped:** R0–R3 (`review-r0-v1` … `review-r3-v1`). **General plans:** R0–R7 complete. **Next:** R4 — `execution-peer-review` → `phase-execution` on `feat/review-r4-review-run`. **Recovery:** [REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](./REVIEW_PIPELINE_RECOVERY_CHECKLIST.md).

**Program:** [README.md](./README.md) · **Authority (full):** `internal-docs/product/revy/docs/architecture.md`, `WEBHOOKS.md`, `REVY_PRODUCT_SLICE.md`.

---

## Goal

Ship the **Revy review pipeline** additively on the SaaS shell: GitHub App webhooks → repository metadata → PR ingestion → indexing → LLM review → publish → in-app reviewer UI. One repo, feature branches, milestone tags on `main`.

**GitHub App (external):** register and configure per committed runbooks — not code in this repo, but required for live webhooks and API sync.

---

## Build principles

- **Additive** on SaaS shell — no fork; workspace tenancy on all domain rows.
- **GitHub App** webhooks + installation API; Celery queues per [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md).
- **Planning order:** findings (this file) → per-phase **general plan** → **execution** under `waves/` → `phase-execution` on a feature branch.
- **Folder layout:** mirror [docs/saas-base](../saas-base/README.md) — findings + general plans here; execution files under `waves/` only.
- **Hand-written Alembic**; unit tests only (`backend/tests/unit/`).
- **EN+LV** for user-facing strings; `--app-*` tokens.
- **Never block webhook HTTP** on GitHub API — persist + enqueue.

---

## GitHub App — ops docs (committed)

Revy code does not replace GitHub App registration. Use these before expecting webhooks or repo sync to work:

| Doc | When |
|-----|------|
| [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) | Step-by-step create App; minimal permissions for **today** (R0–R1) |
| [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) | Register **once** with full R0–R7 permissions/events (recommended for prod/staging) |
| [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md) | Local smee.io / tunnel, secret alignment, verify delivery |
| [GITHUB_APP_DESCRIPTION.md](../utils/GITHUB_APP_DESCRIPTION.md) | Form copy-paste for App description |

**Env (backend):** `GITHUB_WEBHOOK_SECRET` (R0+); `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY_PATH` (R1 full sync); see `backend/.env.example`.

**Product note:** SaaS shell runs without GitHub configured. Review features degrade gracefully (`503` / skip) until secrets and App are wired.

---

## What exists vs genuinely new

### Verified — shipped in repo

| Layer | Capability | Evidence | Tag |
|-------|------------|----------|-----|
| **P4 Installations** | `github_installations`, list + dev register API/UI | `features/installations/`, migration `0008` | `saas-base-v1` |
| **R0 Webhooks** | `POST /api/v1/webhooks/github`, HMAC, dedupe, `github_events` | `webhooks/github.py`, `0010`, `github_tasks` | `review-r0-v1` |
| **R1 Repositories** | `github_repositories`, webhook apply, `repo_sync`, list/sync API | `github_repositories.py`, `0011`, `repo_tasks` | `review-r1-v1` |
| **R2 Pull requests** | `github_pull_requests`, revisions, `pull_request` webhooks, list API | `github_pull_requests.py`, `0012`, `github_tasks` | `review-r2-v1` |
| **R3 Indexing** | `github_index_jobs`, `github_code_chunks`, Voyage API embeddings (`voyage-3-lite`), semantic search | `github_indexing.py`, `voyage_embeddings.py`, `0013`, `index_tasks` | `review-r3-v1` |
| **GitHub API client** | App JWT + installation token + list repos | `integrations/github_api.py` | `review-r1-v1` |
| **Stripe webhook pattern** | Idempotent ingest (reference) | `webhooks/stripe.py` | SaaS W4 |

### Verified — config / infra

| Item | State |
|------|--------|
| Celery routes | `github_events`, `repo_sync`, `indexing`, `review`, … in `celery_app.py` |
| Worker deploy (CI) | Still `-Q default,notifications,heavy` — document v1 Revy queues in deploy supplement |
| Migrations | `0001`–`0013` on `main` |
| pgvector | Extension in deploy SQL; `github_code_chunks.embedding` vector(512) — **R3 shipped** |

### Genuinely new (R4–R7)

| Phase | Capability |
|-------|------------|
| **R4** | LLM review stages, findings schema |
| **R5** | Reconciliation + judge queues |
| **R6** | GitHub check runs + review comments publish |
| **R7** | `features/reviewer/` UI + dashboard widgets |

### Reuse caveats / traps

| Trap | Detail |
|------|--------|
| **Orphan installation** | Webhook for unknown `github_installation_id` → log + **200**; register via `/installations` first |
| **GitHub optional at runtime** | Empty `GITHUB_WEBHOOK_SECRET` → webhooks disabled; empty App id/key → full sync disabled |
| **OAuth install UI** | Not shipped — manual register (P4) until later phase |
| **`heavy_job`** | Routed in `celery_app.py` but undefined — SaaS carryover |
| **Pre-routed future workers** | `reconcile_tasks`, `judge_tasks`, `publish_tasks` routed in `celery_app.py` but not implemented until R5/R6 |
| **Skipped planning on R0/R1** | Code shipped first; general plans + findings updated retroactively — **do not repeat for R2+** |
| **Greptile remediation** | Open P1/P2 on merged PRs #8–#11 — see [REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](./REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) Track 2 |

---

## Catalog (phased)

| Phase | Capability | General plan | Execution | Status |
|-------|------------|--------------|-----------|--------|
| **R0** | Webhook ingest + HMAC + dedupe + `github_events` | [R0](./REVIEW_PIPELINE_R0_WEBHOOKS_GENERAL_PLAN.md) | [R0 exec](./waves/REVIEW_PIPELINE_R0_EXECUTION.md) | **shipped** |
| **R1** | Repository metadata + `repo_sync` | [R1](./REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md) | [R1 exec](./waves/REVIEW_PIPELINE_R1_EXECUTION.md) | **shipped** |
| **R2** | PR ingestion + revisions | [R2](./REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md) | [R2 exec](./waves/REVIEW_PIPELINE_R2_EXECUTION.md) | **shipped** |
| **R3** | Indexing (chunks, pgvector) | [R3](./REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md) | [R3 exec](./waves/REVIEW_PIPELINE_R3_EXECUTION.md) | **shipped** |
| **R4** | LLM review + findings | [R4](./REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md) | [R4 exec](./waves/REVIEW_PIPELINE_R4_EXECUTION.md) | **next** |
| **R5** | Reconciliation + judge | [R5](./REVIEW_PIPELINE_R5_RECONCILE_JUDGE_GENERAL_PLAN.md) | — | planned |
| **R6** | GitHub publish | [R6](./REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md) | — | planned |
| **R7** | Reviewer UI | [R7](./REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md) | — | planned |

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| Q1 | Same repo vs fork? | **locked** | Same repo; `saas-base-v1` tag |
| Q2 | Webhook path | **locked** | `POST /api/v1/webhooks/github` |
| Q3 | Delivery dedupe store | **locked** | `github_webhook_deliveries` (Stripe pattern) |
| Q4 | Handler response | **locked** | Verify → dedupe → enqueue → **200**; no GitHub API in handler |
| Q5 | R0 event scope | **locked** | `installation`, `installation_repositories`, `push` |
| Q6 | Repository table name | **locked** | `github_repositories` (not generic `repositories`) |
| Q7 | GitHub App registration | **locked** | Committed runbooks in `docs/utils/`; target config for one-time prod setup |
| Q8 | Worker deploy | **locked** | Document v1 queue list; CI worker update when ops ready |
| Q9 | Plan gates on review | **defer** | After R4 — LLM cost gating TBD |
| Q10 | OAuth GitHub App install UI | **defer** | Manual register until post-R2 |
| R2-Q1 | PR table naming | **locked** | `github_pull_requests` + `github_pull_request_revisions` |
| R2-Q2 | `pull_request` actions v1 | **locked** | `opened`, `synchronize`, `closed`, `reopened` |
| R2-Q3 | Unknown repository on PR webhook | **locked** | Log + **200** (orphan policy) |
| R2-Q4 | PR list API | **locked** | `GET …/repositories/{repo_id}/pull-requests` cursor list |
| R2-Q5 | `pull_request_review` v1 | **locked** | Store review activity row; no publish |
| R3-Q1 | Embedding backend v1 | **locked** | **API first:** Voyage (`voyage-3-lite`, dim 512 shipped). **Parallel track:** self-hosted via `EmbeddingBackend` + `REVY_HF_CACHE_PATH` (`jina-embeddings-v2-base-code`, `nomic-embed-code`) — `architecture.md` §11.3.1 |
| R3-Q2 | Embedding env | **locked** | `VOYAGE_API_KEY` + `REVY_EMBEDDING_MODEL` / `REVY_EMBEDDING_DIMENSIONS`; future `REVY_EMBEDDING_BACKEND=voyage\|local` |
| R3-Q3 | Reranker (retrieval) | **defer** | API vs local `bge-reranker-v2-m3` — post-R3 eval (`REVY_RERANKER_BACKEND`) |
| R4-Q1 | Review trigger permission | **locked** | `admin_users` (same as R3 index trigger) |
| R4-Q2 | Concurrent review runs | **locked** | `409 review_in_progress` if pending/processing run exists for revision |
| R4-Q3 | Review prerequisites | **locked** | Latest index job `completed` + `VOYAGE_API_KEY` + `github_api_enabled` + `MOONSHOT_API_KEY` |
| R4-Q4 | Primary LLM / model tiers | **locked** | Moonshot Kimi — `kimi-k2.7-code` (Standard), `kimi-k3` (Deep/Critical). Anthropic Claude = judge / cross-check in **R5** only (`architecture.md` §13–14) |

---

## Edge cases

| Case | Handling |
|------|----------|
| Webhook for unknown `installation_id` | Log + **200** |
| Duplicate `X-GitHub-Delivery` | Idempotent ack |
| Installation `removed` / `suspended` | `github_installations.status` on `installation` event |
| Repo removed from installation | `github_repositories.status = removed` on `installation_repositories` |
| Cross-workspace installation ID conflict | Blocked at register (`ConflictError`) |
| Migrations on pooled DB | **AUTOCOMMIT** in `alembic/env.py` (`saas-base-v1.1`) |

---

## Experiment / verification

| Check | Pass |
|-------|------|
| `alembic upgrade head` | Tables through `0013` + `alembic_version` |
| [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) Step 1–3 | App created, webhook URL + secret set |
| Manual installation register | Row in `github_installations` |
| R0: smee.io / staging → API | **200**, delivery row, Celery `github_events` |
| R1: `installation_repositories` or sync API | Rows in `github_repositories` |
| R2: `pull_request` `opened` delivery | PR row + revision `1` in `github_pull_requests` |
| R3: index revision + chunk search | Index job `completed`; `search_revision_chunks` returns rows |
| R4: trigger review on indexed revision | `github_findings` rows; member list API |
| R7: UI lists findings | EN+LV strings |

---

## Parking lot

- nginx GitHub IP allowlist
- In-app OAuth install redirect + Setup URL
- `heavy_job` task definition or route removal
- Worker autoscaling per queue
- GitHub App registration automation

---

## References

| Path | Role |
|------|------|
| [REVIEW_PIPELINE_PROGRAM.md](./REVIEW_PIPELINE_PROGRAM.md) | Branching, tags, releases |
| [REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](./REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) | Agent recovery + Greptile remediation |
| [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md) | P4 installations |
| [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) | App create + minimal config |
| [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) | Full target permissions/events |
| [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md) | Local webhook dev |
| `backend/app/api/v1/webhooks/stripe.py` | Webhook idempotency pattern |
| `internal-docs/product/revy/docs/WEBHOOKS.md` | Full webhook spec |
