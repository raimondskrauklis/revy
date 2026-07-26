# docs/review-pipeline/waves/REVIEW_PIPELINE_R1_EXECUTION.md

# R1 — Repository sync (execution)

Phase **R1** of [REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md](../REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md). **Depends on** R0 (`review-r0-v1`).

**GitHub App:** [GITHUB_APP_SETUP.md](../../utils/GITHUB_APP_SETUP.md), [GITHUB_APP_TARGET_CONFIG.md](../../utils/GITHUB_APP_TARGET_CONFIG.md) (Metadata + `installation_repositories`).

**Goal:** Mirror installation-linked repository metadata from webhooks and optional GitHub API full sync.

**Authority:** [REVY_PRODUCT_SLICE.md](../../starter-pack/REVY_PRODUCT_SLICE.md), `internal-docs/product/revy/docs/WEBHOOKS.md`.

## Decisions locked for R1

- **Table:** `github_repositories` — FK `installation_id` → `github_installations.id`; unique `(installation_id, github_repository_id)`.
- **Status:** `active` \| `removed` — webhook `installation_repositories` sets removed; full sync reconciles missing rows to `removed`.
- **Webhook path:** extend R0 `process_github_event` — handle `installation_repositories` inline (no second enqueue).
- **Full sync:** `POST …/installations/{id}/sync-repositories` → Celery `repo_sync` when `GITHUB_APP_ID` + key path set; else `503 github_api_disabled`.
- **List API:** `GET …/installations/{id}/repositories` — cursor list, workspace member `items:view`.
- **Out of scope:** clone/mirror file content, branch protection, PR entities (R2).

---

## R1.1 — Schema migration

**What:** Hand-written migration `0011_github_repositories`; `GitHubRepositoryORM`; `GitHubRepositoryStatus` enum.

**Files:** `alembic/versions/…_github_repositories.py`, `models/github_repository.py`, `constants/enums.py`, `models/__init__.py`

**Deliverable:** migration applies on fresh DB.

---

## R1.2 — Repository service + webhook apply

**What:** `services/github_repositories.py` — upsert from webhook repo dict, mark removed, cursor list, reconcile from API list.

**Files:** `services/github_repositories.py`, `schemas/github_repository.py`, tests

**Deliverable:** `pytest tests/unit/test_github_repositories.py -q` — green.

---

## R1.3 — GitHub API client + repo_tasks

**What:** `integrations/github_api.py` — app JWT + list installation repos (paginated). `workers/repo_tasks.py` — `sync_installation_repositories`. Register in `celery_app.py`. Wire `github_tasks` `installation_repositories` handler.

**Files:** `integrations/github_api.py`, `workers/repo_tasks.py`, `workers/github_tasks.py`, `core/config.py` (`github_api_enabled`)

**Deliverable:** `pytest tests/unit/test_github_api.py tests/unit/test_repo_tasks.py -q` — green.

---

## R1.4 — Workspace API

**What:** Nested routes under installations — list repositories, trigger sync (admin).

**Files:** `api/v1/workspaces/repositories.py`, `api/v1/workspaces/__init__.py`, route tests

**Deliverable:** `pytest tests/unit/test_github_repository_routes.py -q` — green.

---

## R1.5 — Docs sync

**What:** Update program index; note `GITHUB_APP_ID` + private key for full sync in `GITHUB_WEBHOOK_DEV.md`.

**Files:** `docs/review-pipeline/waves/README.md`, `REVIEW_PIPELINE_PROGRAM.md`

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_repositories.py \
  tests/unit/test_github_api.py \
  tests/unit/test_repo_tasks.py \
  tests/unit/test_github_repository_routes.py \
  tests/unit/test_github_tasks.py \
  -q
```

**Deploy:** `alembic upgrade head`; optional GitHub App credentials for full sync.

**Next:** [REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md](../REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md) → create [REVIEW_PIPELINE_R2_EXECUTION.md](./REVIEW_PIPELINE_R2_EXECUTION.md) when planning R2.
