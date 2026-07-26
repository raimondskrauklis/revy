# R8 — Automation + triggers (execution)

Phase **R8** of [REVIEW_PIPELINE_R8_AUTOMATION_GENERAL_PLAN.md](../REVIEW_PIPELINE_R8_AUTOMATION_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md) § Q11, R8-Q1–R8-Q7. **Depends on** R7 (`review-r7-v1` on `main`).

**Goal:** Autostart index → review → reconcile → publish on PR open/update; `@revy review` on-demand; workspace toggle; single-PR read API.

**Authority:** [GITHUB_APP_TARGET_CONFIG.md](../../utils/GITHUB_APP_TARGET_CONFIG.md) (add `issue_comment` subscribe), [GITHUB_WEBHOOK_DEV.md](../GITHUB_WEBHOOK_DEV.md).

## Decisions locked for R8

- **R8-Q1:** `workspaces.review_autostart_enabled` boolean, default `true`; admin PATCH only.
- **R8-Q2:** Autostart on `pull_request` actions `opened` and `synchronize` only — not standalone `push` (v1). On `synchronize`, enqueue **only when a new revision row was created** (same `head_sha` → no pipeline).
- **R8-Q3:** On-demand **`@revy review`** in `issue_comment` on an **open** PR → full pipeline for PR `head_sha` revision; `action=created` only (ignore `edited`); ignore comments from `REVY_BOT_LOGIN` when set; skip closed/draft PRs.
- **R8-Q4:** Pipeline chain: index (revision) → on index `completed` enqueue review → existing R4→R5→R6 hooks. When prerequisites missing (`github_api_enabled`, `VOYAGE_API_KEY`, `MOONSHOT_API_KEY`), orchestrator logs and returns — no failed-job spam. Webhook HTTP stays **200** (R0); skips happen in worker/orchestrator only.
- **R8-Q5:** `index_in_progress` guard — `409 index_in_progress` on duplicate index trigger (mirror R4 `review_in_progress`).
- **R8-Q6:** `GET …/repositories/{repo_id}/pull-requests/{pull_request_id}` — member read; replaces cursor scan in reviewer detail hook.
- **R8-Q7:** **Manual index isolation** — admin `POST …/index` sets `trigger_source=manual` on the index job; index-complete hook does **not** enqueue review. Only `trigger_source ∈ {autostart, command}` chains index → review.
- **Schema:** Migration `0017` adds `workspaces.review_autostart_enabled` and `github_index_jobs.trigger_source` enum (`manual` \| `autostart` \| `command`) — single revision, no split migration.
- **Webhook:** add `issue_comment` to `SUPPORTED_EVENTS`; handler enqueues pipeline only per R8-Q3.
- **Orchestrator:** `services/review_pipeline.py` — `maybe_enqueue_pipeline_for_revision(session, *, workspace_id, revision_id, trigger: autostart | command)`; `enqueue_review_for_revision` when index job `trigger_source` is `autostart` or `command`.
- **Enqueue timing:** Celery tasks enqueued **after** DB commit — mirror `installation_indexing.py` (`commit` then `delay`); in `github_tasks`, collect intents in `_run()`, enqueue in sync code **after** `asyncio.run()` returns.
- **Out of scope:** `@revy index`, `@revy publish`; draft-PR-only autostart mode; path/label filters; incremental index (R9).

## Out of scope for R8 (later)

- Incremental chunk hash index → **R9**
- Evidence snippet on findings → **R9**
- Email on review complete → **R9**
- `push` event autostart → parking lot
- Publish inline retry / `inline_comments_posted` flag → parking lot (Greptile R6 edge case)

---

## R8.1 — Workspace autostart setting

**What:** Migration `0017` — `workspaces.review_autostart_enabled` NOT NULL default `true`; `github_index_jobs.trigger_source` NOT NULL default `manual`; expose autostart on `WorkspaceResponse` / `WorkspaceUpdate` (optional fields: at least one of `name` or `review_autostart_enabled` required); audit `workspace.review_autostart_updated` when toggle changes.

**Files:** `alembic/versions/…_0017_workspace_review_autostart.py`, `models/workspaces.py`, `models/github_index_job.py`, `constants/enums.py`, `schemas/workspaces.py`, `services/workspaces.py`, `api/v1/workspaces/settings.py`, `tests/unit/test_workspaces.py`

**Deliverable:** `pipenv run pytest tests/unit/test_workspaces.py -q`

**LOOP pause:** hand-written Alembic revision.

---

## R8.2 — Pipeline orchestrator

**What:** `services/review_pipeline.py` — `maybe_enqueue_pipeline_for_revision(session, *, workspace_id, revision_id, trigger: autostart | command)` checks autostart flag (skip for `command`), API keys (R8-Q4), `index_in_progress` / `review_in_progress`; creates index job with `trigger_source=trigger`; enqueues index Celery task after caller commits. `create_index_job` (admin API) always sets `trigger_source=manual`.

**Files:** `services/review_pipeline.py`, `services/github_indexing.py`, `tests/unit/test_review_pipeline.py`

**Deliverable:** `pipenv run pytest tests/unit/test_review_pipeline.py -q`

---

## R8.3 — Index-complete → review chain

**What:** Hook `index_tasks` on job `completed` → call `enqueue_review_for_revision` only when `job.trigger_source in (autostart, command)` and index status is `completed`.

**Files:** `workers/index_tasks.py`, `services/review_pipeline.py`, `tests/unit/test_index_tasks.py`, `tests/unit/test_review_pipeline.py`

**Deliverable:** `pipenv run pytest tests/unit/test_index_tasks.py tests/unit/test_review_pipeline.py -q`

---

## R8.4 — PR webhook autostart

**What:** Extend `apply_pull_request_webhook_event` (or helper) to return whether a **new revision** was created and its `revision_id`. In `process_github_event`, after `asyncio.run()` (post-commit), call `maybe_enqueue_pipeline_for_revision(..., trigger=autostart)` for `opened` / `synchronize` when `new_revision=True` and workspace autostart is on.

**Files:** `workers/github_tasks.py`, `services/github_pull_requests.py`, `tests/unit/test_github_tasks_autostart.py`

**Deliverable:** `pipenv run pytest tests/unit/test_github_tasks_autostart.py -q`

---

## R8.5 — `@revy review` + single-PR API

**What:** Add `issue_comment` to `SUPPORTED_EVENTS`; handler parses `@revy review` per R8-Q3; `GET …/pull-requests/{pull_request_id}` on `installation_pull_requests.py`; frontend `usePullRequest` calls single-PR fetch (remove page scan).

**Files:** `services/github_webhooks.py`, `workers/github_tasks.py`, `api/v1/workspaces/installation_pull_requests.py`, `services/github_pull_requests.py`, `features/reviewer/api.ts`, `features/reviewer/hooks.ts`, `tests/unit/test_github_webhooks.py`, `tests/unit/test_github_pull_request_routes.py`, i18n if new error strings

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_webhooks.py tests/unit/test_github_pull_request_routes.py -q
cd frontend && npm test -- src/features/reviewer/hooks.test.ts
```

---

## R8.6 — Settings UI + doc sync

**What:** Workspace settings toggle (EN+LV) for autostart; update `GITHUB_WEBHOOK_DEV.md` § autostart + `@revy review`; `GITHUB_APP_TARGET_CONFIG.md` — move **Issue comment** to subscribed events; findings Q11 → shipped; program README + recovery Track G; fix `REVIEW_PIPELINE_PRODUCT_PATTERNS.md` incremental index → **R9**.

**Files:** `frontend/src/features/settings/…`, `i18n`, `docs/review-pipeline/*`, `docs/utils/GITHUB_APP_TARGET_CONFIG.md`

**Deliverable:**

```bash
cd frontend && npm run lint && npm test && npm run build
```

**Human gate:** staging e2e — open PR → autostart chain; comment `@revy review` → re-run; toggle autostart off → manual only; admin `POST …/index` does not auto-review.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_workspaces.py \
  tests/unit/test_review_pipeline.py \
  tests/unit/test_index_tasks.py \
  tests/unit/test_github_tasks_autostart.py \
  tests/unit/test_github_webhooks.py \
  tests/unit/test_github_pull_request_routes.py -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- src/features/reviewer/ && npm run build
```

**Deploy:** `alembic upgrade head` (`0017`); GitHub App subscribe **Issue comments**; worker queues unchanged (R4–R6 routes).

**Tag on `main`:** `review-r8-v1`

**Next:** none — R9 general plan when incremental index scoped.
