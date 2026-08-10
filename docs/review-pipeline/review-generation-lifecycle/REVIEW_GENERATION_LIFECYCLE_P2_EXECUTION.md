# Review generation lifecycle P2 — Supersede + stage-entry guards (execution)

Phase **P2** of [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](./REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md). Baseline: findings RG-2, RG-7, RG-8, RG-11, RG-Q8, RG-Q11. **P2 only.**

**Goal:** New `synchronize` supersedes prior generations; authority at index/review/publish entry; stale G10 checks finalized at supersede moment.

## Decisions locked for P2

- On `synchronize` after revision create: `mark_review_runs_superseded_for_pull_request` + `mark_index_jobs_superseded_for_pull_request` + finalize G10 neutral for each superseded in-flight pipeline linked to those review runs **or** index jobs.
- On same-SHA `synchronize` or `@revy review`: `supersede_active_generations_for_revision` clears in-flight review runs **and** index jobs on the HEAD revision before enqueue.
- `apply_resolution_status_for_synchronize` runs in Celery task `apply_resolution_for_synchronize` (scheduled from `process_github_event` on `synchronize`) — **not** inline on the webhook worker (RG-15). Non-coalesce: index `enqueue_index_job` deferred until resolution `applied`. Coalesce: autostart scheduled after resolution with event-anchored `coalesce_schedule_at` (see [P4](./REVIEW_GENERATION_LIFECYCLE_P4_EXECUTION.md)).
- `index_pull_request_revision`: before `start_pipeline_github_check`, if not `is_authoritative_for_pull_request_head` → skip G10 + `ensure_pipeline_run_for_index_job` / stash (index `run_index_job` may still execute — RG-Q11).
- `prepare_review_after_index`: if not authoritative → return `ReviewAfterIndexOutcome()` without `create_review_run`.
- `reconcile_tasks.py`: after reconcile, if review run `superseded` → skip `enqueue_publish_for_review_run`.
- `@revy review` on same PR: on **command** enqueue (`issue_comment` path), call `supersede_active_generations_for_revision` for current HEAD revision before `maybe_enqueue_pipeline_for_revision` (supersedes autostart in-flight review runs **and** index jobs on same revision).
- PRODUCT_PATTERNS generation row → **in flight** (link to this program).

## Out of scope for P2

- Full surface flush → **P3**
- Coalesce debounce → **P4**
- Judge filter → **P5**

---

## P2.1 — Supersede hook on synchronize

**What:** In `apply_pull_request_webhook_event` synchronize path (after `new_revision` flush): call `supersede_stale_generations_for_new_revision` then `supersede_active_generations_for_revision`; for each returned superseded review run or index job, load pipeline run and `finalize_pipeline_github_check_neutral`. Schedule `apply_resolution_for_synchronize` from `process_github_event` (not inline here).

**Files:** `backend/app/services/github_pull_requests.py`, `backend/app/workers/github_tasks.py`, `backend/app/services/github_generation_lifecycle.py`, `backend/app/services/github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_generation_lifecycle.py -k "supersede_on_synchronize or mark_review_runs" -q
```

---

## P2.2 — Index task authority guard

**What:** In `index_pull_request_revision`, wrap the **entire pipeline-trace + G10 block** (`ensure_pipeline_run_for_index_job`, `start_pipeline_github_check`, `stash_pipeline_github_check_run_id`) — run only when `is_authoritative_for_pull_request_head(session, revision_id=pending_job.revision_id)`. When not authoritative: skip pipeline run creation and G10; `run_index_job` may still execute (RG-Q11). Log `pipeline_index_skipped_not_authoritative`.

**Files:** `backend/app/workers/index_tasks.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_index_tasks_generation.py -q
```

---

## P2.3 — Review enqueue authority guard

**What:** In `prepare_review_after_index`, after draft/closed check, if not authoritative → log and return empty outcome (no `create_review_run`).

**Files:** `backend/app/services/review_pipeline.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_review_pipeline.py -k "not_authoritative or prepare_review_after_index" -q
```

---

## P2.4 — Publish enqueue supersede guard

**What:** In `reconcile_tasks.py` inside `_run()`, **before** `session.commit()` and **before** `enqueue_publish_for_review_run`: load review run; if `superseded`, log `publish_enqueue_skipped_superseded` and return without enqueue. Belt-and-suspenders with P1 `run_publish_job` check.

**Files:** `backend/app/workers/reconcile_tasks.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_reconcile_tasks_generation.py -q
```

---

## P2.5 — Command supersede (same revision)

**What:** In `process_github_event` `issue_comment` path, before `maybe_enqueue_pipeline_for_revision` with `trigger=command`: call `supersede_active_generations_for_revision(session, revision_id=…)` so `@revy review` wins over autostart on same HEAD (review runs + index jobs).

**Files:** `backend/app/workers/github_tasks.py`, `backend/app/services/github_generation_lifecycle.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_tasks_autostart.py -k "command_supersedes or revy_review" -q
```

---

## P2.6 — End-to-end unit scenario + PRODUCT_PATTERNS

**What:** Test: enqueue H1 index task; supersede via H2 synchronize hook; H1 index runs later → no `ensure_pipeline_run_for_index_job` and no `start_pipeline_github_check` for H1. Update PRODUCT_PATTERNS “Snapshot generation at HEAD” row to **in flight** with link.

**Files:** `backend/tests/unit/test_github_generation_lifecycle.py`, `docs/review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_generation_lifecycle.py tests/unit/test_index_tasks_generation.py tests/unit/test_reconcile_tasks_generation.py -q
```

---

## P2.7 — Post-ship restart hotfix (PR #89)

**Symptom (staging 2026-08):** Push while Revy `in_progress`, or `@revy review` while pipeline running → no new run in UI; worker logs show webhook received but no enqueue until worker restart.

**Root cause (RG-15):**

1. P2 supersede marked **review runs** only — pending/processing **index jobs** left `maybe_enqueue_pipeline_for_revision` returning `None` (`pipeline_index_in_progress`).
2. `apply_resolution_status_for_synchronize` ran **inline** in the `github_events` worker (compare + per-file HEAD checks) before enqueue — could block the queue for minutes.

**Shipped fix ([PR #89](https://github.com/raimondskrauklis/revy/pull/89)):**

- **Index supersede** — `mark_*_index_jobs_superseded_*` CAS `pending`/`processing` → `failed` with shared message `Superseded by newer run` (`app/constants/github_messages.py`); batch G10 neutralize via `finalize_pipeline_checks_for_superseded_index_jobs`.
- **Same-SHA retrigger** — `supersede_active_generations_for_revision` on every `synchronize` (and before `@revy review` enqueue); `PullRequestWebhookResult.pipeline_retrigger` for same-HEAD `synchronize`.
- **Deferred resolution pairing** — `apply_resolution_for_synchronize` Celery task (not inline on `github_events` worker):
  - **Non-coalesce (`review_coalesce_seconds=0`):** webhook creates pending index job; `enqueue_index_job` runs only after resolution `applied` (G9 stamps before pipeline starts).
  - **Coalesce (`review_coalesce_seconds>0`):** resolution runs immediately; `schedule_autostart_pipeline_for_revision` is scheduled **after** resolution `applied` with `coalesce_schedule_at` anchored to the **synchronize** event (preserves ≤10 s quiet window even when compare is slow).
- **Authority + cleanup** — resolution task checks `is_authoritative_for_pull_request_head`; on `skipped_stale` / `skipped_permanent` / exhausted retries, pending follow-up index jobs are failed and linked G10 checks finalized (when still `pending`).
- **Coalesce stale handoff** — when a coalesce resolution task is `skipped_stale`, re-dispatch `apply_resolution_for_synchronize` for PR HEAD (`resolution-synchronize-{revision_id}` task id) so autostart still chains through pairing (never schedule autostart directly from a stale task).
- **Stable Celery task ids** — `coalesce-autostart-{workspace_id}-{revision_id}` dedupes coalesce timers; `resolution-synchronize-{revision_id}` dedupes HEAD handoff vs duplicate webhooks.
- **Index worker hardening** — atomic CAS claim `pending`→`processing`; CAS complete `processing`→`completed`; delete orphaned chunks when superseded mid-run.
- **Moonshot transient errors** — Cloudflare gateway **520–524** added to `RETRYABLE_HTTP_STATUS_CODES` (`worker_retries.py`) so review runs Celery-retry instead of failing on one-off `api.moonshot.ai` 520s.

**Revy:** clean on PR #89 (2026-08-10).

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_generation_lifecycle.py tests/unit/test_github_tasks_autostart.py tests/unit/test_github_indexing.py -k "supersede or synchronize or coalesce or resolution" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check .
pipenv run pytest tests/unit/test_github_generation_lifecycle.py tests/unit/test_index_tasks_generation.py tests/unit/test_review_pipeline.py tests/unit/test_reconcile_tasks_generation.py tests/unit/test_github_tasks_autostart.py -k "not_authoritative or prepare_review_after_index or supersede or command_supersedes" -q
```

**Next:** [REVIEW_GENERATION_LIFECYCLE_P3_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P3_EXECUTION.md)
