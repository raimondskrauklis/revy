# docs/review-pipeline/waves/REVIEW_PIPELINE_R2_EXECUTION.md

# R2 — Pull request ingestion (execution)

Phase **R2** of [REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md](../REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md). **Depends on** R1 (`review-r1-v1`).

**GitHub App:** [GITHUB_APP_TARGET_CONFIG.md](../../utils/GITHUB_APP_TARGET_CONFIG.md) § R2 — subscribe **Pull request**, **Pull request review**; Pull requests Read and write permission.

**Goal:** Track pull requests, per-push revisions, and review activity from GitHub webhooks; workspace-scoped list API.

**Authority:** `internal-docs/product/revy/docs/WEBHOOKS.md`, [GITHUB_WEBHOOK_DEV.md](../GITHUB_WEBHOOK_DEV.md).

## Decisions locked for R2

- **Tables:** `github_pull_requests`, `github_pull_request_revisions`, `github_pull_request_reviews`.
- **PR identity:** unique `(repository_id, github_pull_request_id)` where `github_pull_request_id` = GitHub global PR `id`.
- **Revisions:** insert row on `opened` (revision `1`) and each `synchronize`; monotonic `revision_number` per PR.
- **PR state:** `open` \| `closed` from `pull_request.state`; update on `closed` / `reopened`.
- **Webhook events:** add `pull_request`, `pull_request_review` to `SUPPORTED_EVENTS`; handle in `github_tasks` (no new queue).
- **`pull_request` actions v1:** `opened`, `synchronize`, `closed`, `reopened` — ignore others (log).
- **`pull_request_review` actions v1:** `submitted`, `edited`, `dismissed` — store review row keyed by GitHub review `id`.
- **Orphan repository:** unknown `repository.id` for installation → log warning + return (delivery already **200**).
- **List API:** `GET /api/v1/workspaces/{workspace_id}/repositories/{repository_id}/pull-requests` — cursor list, `items:view`.
- **Out of scope:** diff storage, inline comments, publish (R6), `push` → re-review (R3/R4).

---

## R2.1 — Schema migration

**What:** Hand-written migration `0012_github_pull_requests`; ORM models; enums `GitHubPullRequestState`, `GitHubPullRequestReviewState`.

**Files:** `alembic/versions/…_github_pull_requests.py`, `models/github_pull_request.py`, `models/github_pull_request_revision.py`, `models/github_pull_request_review.py`, `constants/enums.py`, `models/__init__.py`

**Deliverable:** `alembic upgrade head` on fresh DB creates tables.

---

## R2.2 — PR service + webhook apply

**What:** `services/github_pull_requests.py` — resolve repo by `github_repository_id` + installation; upsert PR; append revision; apply `pull_request_review` events.

**Files:** `services/github_pull_requests.py`, `schemas/github_pull_request.py`, `tests/unit/test_github_pull_requests.py`

**Deliverable:** `pytest tests/unit/test_github_pull_requests.py -q` — green.

---

## R2.3 — Webhook wiring

**What:** Extend `SUPPORTED_EVENTS`; `github_tasks` handlers for `pull_request` and `pull_request_review`.

**Files:** `services/github_webhooks.py`, `workers/github_tasks.py`, `tests/unit/test_github_tasks.py`, `tests/unit/test_github_webhook.py`

**Deliverable:** webhook tests pass for new event types.

---

## R2.4 — Workspace list API

**What:** `GET …/repositories/{repository_id}/pull-requests` — verify repo belongs to workspace; cursor list active PRs.

**Files:** `api/v1/workspaces/installation_pull_requests.py`, `api/v1/workspaces/__init__.py`, `tests/unit/test_github_pull_request_routes.py`

**Deliverable:** `pytest tests/unit/test_github_pull_request_routes.py -q` — green.

---

## R2.5 — Docs sync

**What:** Update waves README, findings verification row, `GITHUB_WEBHOOK_DEV.md` § PR events smoke test.

**Files:** `docs/review-pipeline/waves/README.md`, `docs/review-pipeline/GITHUB_WEBHOOK_DEV.md`

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_pull_requests.py \
  tests/unit/test_github_pull_request_routes.py \
  tests/unit/test_github_webhook.py \
  tests/unit/test_github_tasks.py \
  -q
```

**Deploy:** `alembic upgrade head`; GitHub App subscribed to Pull request + Pull request review events.

**Human gate:** one synthetic or real `pull_request` `opened` delivery → row in `github_pull_requests` + revision `1`.

**Next:** [REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md](../REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md) → create [REVIEW_PIPELINE_R3_EXECUTION.md](./REVIEW_PIPELINE_R3_EXECUTION.md) when planning R3.
