# GitHub surface P2 — L1 presence (execution)

Phase **P2** of [POST_REVIEW_QUALITY_GENERAL_PLAN.md](./POST_REVIEW_QUALITY_GENERAL_PLAN.md). Baseline: [POST_REVIEW_QUALITY_FINDINGS.md](./POST_REVIEW_QUALITY_FINDINGS.md) §4 L1, RQ9 neutral finalize. **P2 only.**

**Goal:** PR feels “under review” before publish completes — G10 `in_progress` → `completed`; optional Greptile-class ack.

**Authority:** `backend/app/services/github_pipeline_trace.py` · `backend/app/workers/index_tasks.py`

## Decisions locked for P2

- G10 check created at pipeline start (`start_pipeline_github_check`, `status=in_progress`).
- Publish updates **same** `github_check_run_id` when pipeline link exists (`create_publish_job_for_review_run`).
- RQ9 neutral finalize on draft/closed after index — already shipped; verify only.
- Ack comment (👀 class) is **optional** — explicit defer OK in dogfood.
- Orphan second check-run — log in dogfood, fix not required for P2 gate.

## Out of scope for P2 (later phases)

- L2 formatter copy → **P1** (done)
- Inline warnings → **P3**
- Draft autostart (skipped by design)
- Orphan-check production hardening → deferred log

---

## P2.1 — Pipeline check starts in_progress

**What:** Add `test_start_pipeline_github_check_creates_in_progress_run`: mock `github_api.create_check_run` with `status="in_progress"` and summary containing “Revy review in progress”.

**Files:** `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py::test_start_pipeline_github_check_creates_in_progress_run -q
```

---

## P2.2 — Publish reuses pipeline check id

**What:** Add `test_create_publish_job_for_review_run_reuses_pipeline_check_id`: pipeline run has `github_check_run_id`; new publish job copies it onto `GitHubPublishJobORM.github_check_run_id`. Separate test or extend publish job test: `run_publish_job` calls `update_check_run` on that id (not `create_check_run`) when linked.

**Files:** `backend/tests/unit/test_github_publish.py`, `backend/app/services/github_publish.py` (fix only if gap)

**Deliverable:**

```bash
cd backend && pipenv run pytest \
  tests/unit/test_github_publish.py::test_create_publish_job_for_review_run_reuses_pipeline_check_id \
  tests/unit/test_github_publish.py::test_run_publish_job_updates_linked_pipeline_check_run -q
```

---

## P2.3 — RQ9 neutral finalize regression

**What:** Keep draft-after-index neutral path green (`prepare_review_after_index`, `index_tasks`).

**Files:** `backend/tests/unit/test_review_pipeline.py`, `backend/tests/unit/test_index_tasks.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_review_pipeline.py tests/unit/test_index_tasks.py -q -k "neutral or draft"
```

---

## P2.4 — Optional ack on `@revy review` (ship or defer)

**What:** If shipping: short issue comment or reaction-style ack when `issue_comment` command received (`trigger=command`), before pipeline completes. If deferring: one line in dogfood “ack deferred P2.4” — **locked defer deliverable**.

**Files:** `backend/app/services/github_pull_requests.py` or new `github_review_ack.py`, `backend/app/integrations/github_api.py`, tests in `backend/tests/unit/`

**Deliverable (if shipped):**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pull_requests.py::test_issue_comment_review_posts_ack -q
```

**Deliverable (if deferred):** dogfood note only — no test required.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_pipeline_trace.py::test_start_pipeline_github_check_creates_in_progress_run \
  tests/unit/test_github_publish.py::test_create_publish_job_for_review_run_reuses_pipeline_check_id \
  tests/unit/test_github_publish.py::test_run_publish_job_updates_linked_pipeline_check_run \
  tests/unit/test_review_pipeline.py tests/unit/test_index_tasks.py -q -k "neutral or draft"
```

**Human gate:** Dogfood L1 = Y on PR push (check visible early, sensible completion). **Non-gate** for commit.

**Next:** [GITHUB_SURFACE_P3_EXECUTION.md](./GITHUB_SURFACE_P3_EXECUTION.md)
