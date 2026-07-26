# R8 — Automation + triggers (execution)

Phase **R8** of [REVIEW_PIPELINE_R8_AUTOMATION_GENERAL_PLAN.md](../REVIEW_PIPELINE_R8_AUTOMATION_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md) § Q11, R8-Q1–R8-Q6. **Depends on** R7 (`review-r7-v1` on `main`).

**Goal:** Autostart index → review → reconcile → publish on PR open/update; `@revy review` on-demand; workspace toggle; single-PR read API.

**Authority:** [GITHUB_APP_TARGET_CONFIG.md](../../utils/GITHUB_APP_TARGET_CONFIG.md) (add `issue_comment` subscribe), [GITHUB_WEBHOOK_DEV.md](../GITHUB_WEBHOOK_DEV.md).

## Decisions locked for R8

- **R8-Q1:** `workspaces.review_autostart_enabled` boolean, default `true`; admin PATCH only.
- **R8-Q2:** Autostart on `pull_request` actions `opened` and `synchronize` only — not standalone `push` (v1).
- **R8-Q3:** On-demand command **`@revy review`** in `issue_comment` on a PR → full pipeline for PR `head_sha` revision; match bot login from `REVY_BOT_LOGIN` when set (ignore self-comments from bot).
- **R8-Q4:** Pipeline chain: index (revision) → on index `completed` enqueue review → existing R4→R5→R6 hooks; skip chain when prerequisites missing (`github_api_enabled`, `VOYAGE_API_KEY`, `MOONSHOT_API_KEY`) — log + **200** webhook, no failed jobs spam.
- **R8-Q5:** `index_in_progress` guard — `409 index_in_progress` on duplicate index trigger (mirror R4 `review_in_progress`).
- **R8-Q6:** `GET …/repositories/{repo_id}/pull-requests/{pull_request_id}` — member read; replaces cursor scan in reviewer detail hook.
- **Webhook:** add `issue_comment` to `SUPPORTED_EVENTS`; handler enqueues pipeline only for created/edited comments containing `@revy review`.
- **Orchestrator:** `services/review_pipeline.py` — single entry `maybe_enqueue_pipeline_for_revision(...)` used by webhook autostart and `@revy` path; respects autostart flag + guards.
- **Out of scope:** `@revy index`, `@revy publish`; draft-PR-only mode; path/label filters; incremental index (R9).

## Out of scope for R8 (later)

- Incremental chunk hash index → **R9**
- Evidence snippet on findings → **R9**
- Email on review complete → **R9**
- `push` event autostart → parking lot
- Publish inline retry / `inline_comments_posted` flag → parking lot (Greptile R6 edge case)

---

## R8.1 — Workspace autostart setting

**What:** Migration `0017` — `workspaces.review_autostart_enabled` NOT NULL default true; expose on `WorkspaceResponse` / `WorkspaceUpdate`; audit `workspace.review_autostart_updated`.

**Files:** `alembic/versions/…_0017_workspace_review_autostart.py`, `models/workspaces.py`, `schemas/workspaces.py`, `services/workspaces.py`, `tests/unit/test_workspaces.py`

**Deliverable:** `pipenv run pytest tests/unit/test_workspaces.py -q`

**LOOP pause:** hand-written Alembic revision.

---

## R8.2 — Pipeline orchestrator

**What:** `services/review_pipeline.py` — `maybe_enqueue_pipeline_for_revision(session, *, workspace_id, revision_id, trigger: autostart | command)` — checks autostart flag (skip for `command`), API keys, `index_in_progress` / `review_in_progress`; enqueues `index_revision` Celery task when allowed.

**Files:** `services/review_pipeline.py`, `tests/unit/test_review_pipeline.py`

**Deliverable:** `pipenv run pytest tests/unit/test_review_pipeline.py -q`

---

## R8.3 — Index-complete → review chain

**What:** Hook `index_tasks` on job `completed` → call orchestrator stage-2 `enqueue_review_for_revision` when autostart chain active (store `trigger_source` on index job metadata or infer latest revision — prefer explicit `github_index_jobs.trigger_source` enum column in `0017` or `0018` if needed).

**Files:** `workers/index_tasks.py`, `models/github_index_job.py`, `services/review_pipeline.py`, tests

**Deliverable:** `pipenv run pytest tests/unit/test_index_tasks.py tests/unit/test_review_pipeline.py -q`

---

## R8.4 — PR webhook autostart

**What:** After `apply_pull_request_webhook_event` for `opened` / `synchronize`, resolve latest revision id → `maybe_enqueue_pipeline_for_revision(..., trigger=autostart)` inside `github_tasks` (post-commit enqueue only).

**Files:** `workers/github_tasks.py`, `services/github_pull_requests.py` (if revision id helper needed), `tests/unit/test_github_tasks_autostart.py`

**Deliverable:** `pipenv run pytest tests/unit/test_github_tasks_autostart.py -q`

---

## R8.5 — `@revy review` + single-PR API

**What:** Add `issue_comment` to `SUPPORTED_EVENTS`; handler parses `@revy review`; `GET …/pull-requests/{pull_request_id}` route; frontend `usePullRequest` calls single-PR fetch (remove page scan).

**Files:** `services/github_webhooks.py`, `workers/github_tasks.py`, `api/v1/workspaces/installation_review.py`, `features/reviewer/api.ts`, `hooks.ts`, `tests/unit/…`, i18n if new error strings

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_webhooks.py tests/unit/test_github_pull_request_routes.py -q
cd frontend && npm test -- src/features/reviewer/hooks.test.ts
```

---

## R8.6 — Settings UI + doc sync

**What:** Workspace settings toggle (EN+LV) for autostart; update `GITHUB_WEBHOOK_DEV.md` § autostart + `@revy review`; `GITHUB_APP_TARGET_CONFIG.md` `issue_comment` event; findings Q11 → shipped; program README + recovery Track G.

**Files:** `frontend/src/features/settings/…`, `i18n`, `docs/review-pipeline/*`

**Deliverable:**

```bash
cd frontend && npm run lint && npm test && npm run build
```

**Human gate:** staging e2e — open PR → autostart chain; comment `@revy review` → re-run; toggle autostart off → manual only.

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

**Deploy:** `alembic upgrade head` (`0017`+); GitHub App subscribe **Issue comments**; worker queues unchanged (R4–R6 routes).

**Tag on `main`:** `review-r8-v1`

**Next:** none — R9 general plan when incremental index scoped.
