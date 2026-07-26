# docs/review-pipeline/waves/REVIEW_PIPELINE_R6_EXECUTION.md

# R6 — GitHub publish (execution)

Phase **R6** of [REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md](../REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md). **Depends on** R5 (`review-r5-v1`).

**Goal:** Publish reconciled findings to GitHub check runs and PR comments — idempotent per `head_sha`.

**Authority:** [GITHUB_APP_TARGET_CONFIG.md](../../utils/GITHUB_APP_TARGET_CONFIG.md) § R6, [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) § R6 execution open items.

## Decisions locked for R6

- **Table:** `github_publish_jobs` — links `review_run_id`, `revision_id`, `head_sha`, `github_check_run_id`, `github_comment_id`, status, error.
- **Queue:** `publish_tasks` on `github_publish` (route exists).
- **Trigger:** enqueue after R5 reconcile+judge complete for run; admin may also `POST …/publish` for retry (`admin_users`).
- **Check run name:** `revy/review` (stable per installation).
- **`external_id`:** `revy:{github_installation_id}:{github_pr_number}:{head_sha}` on create (`github_installation_id` = GitHub numeric id from `github_installations`, not internal UUID); reuse GitHub check run id on update.
- **Idempotency (R6-Q1):** update existing check run + stored PR summary comment for same `head_sha`; new `head_sha` → new check run (do not mutate prior SHA).
- **Conclusion (R6-Q2):** `failure` if any active group has `critical` or `error`; `success` if no `error`/`critical` active groups; `neutral` if only `warning`/`info`; map to GitHub `conclusion` enum.
- **Summary body:** markdown table of active reconciled findings (cap 50 rows); link to Revy UI.
- **Inline v1:** post review comments only for `error` + `critical` with valid `file_path` + `start_line`; rest summary-only.
- **PR comment:** update bot summary comment via stored `github_comment_id`; create once per `head_sha` then update.
- **Out of scope:** suggestion blocks (R6-Q3 defer); annotations on every line; numeric 0–5 score; `check_run` webhook subscribe (optional follow-up).

---

## R6.1 — Schema migration

**What:** Migration `0016_github_publish_jobs`; `GitHubPublishJobORM`; `GitHubPublishJobStatus` enum.

**Files:** `alembic/versions/…_github_publish_jobs.py`, models, enums

**Deliverable:** migration applies.

**LOOP pause:** hand-written Alembic revision.

---

## R6.2 — GitHub API publish client

**What:** Extend `integrations/github_api.py` — create/update check run; create/update PR review comment; map finding → comment body.

**Files:** `integrations/github_api.py`, `tests/unit/test_github_api_publish.py`

**Deliverable:** unit tests with httpx mocks for Checks + Pull Request Reviews endpoints.

---

## R6.3 — Publish service

**What:** `services/github_publish.py` — load reconciled findings; build summary markdown; compute conclusion; idempotent create/update.

**Files:** `services/github_publish.py`, `schemas/github_publish.py`, `tests/unit/test_github_publish.py`

**Deliverable:** tests cover first publish, update same SHA, new SHA creates new check run.

---

## R6.4 — Publish worker

**What:** `workers/publish_tasks.py` — `publish_review_run(publish_job_id)`; retry with backoff; import in `celery_app.py`.

**Files:** `workers/publish_tasks.py`, `tests/unit/test_publish_tasks.py`

**Deliverable:** worker tests green.

---

## R6.5 — API + verification docs

**What:** Optional admin retry route; member read publish status on review run; update `GITHUB_WEBHOOK_DEV.md` § publish verification.

**Files:** routes, tests, docs

**Deliverable:** phase gate green.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_api_publish.py \
  tests/unit/test_github_publish.py \
  tests/unit/test_publish_tasks.py \
  tests/unit/test_github_publish_routes.py \
  -q
```

**Deploy:** `alembic upgrade head`; GitHub App Checks + Pull requests write; worker `-Q` includes `github_publish`; `REVY_BOT_LOGIN` set.

**Human gate:** publish to test PR; re-run on same SHA updates check in place; new commit creates new check.

**Next:** [REVIEW_PIPELINE_R7_EXECUTION.md](./REVIEW_PIPELINE_R7_EXECUTION.md).
