# Review generation lifecycle P4 — Autostart coalesce (execution)

Phase **P4** of [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](./REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md). Baseline: findings RG-4, RG-Q3. **P4 only.**

**Goal:** Optional debounced autostart — ≤10 s quiet after last `synchronize` before pipeline enqueue.

## Decisions locked for P4

- **Default `review_coalesce_seconds=0`** — coalesce off; no behavior change until configured.
- When `review_coalesce_seconds > 0`: only **`pull_request.synchronize` autostart** path debounced; `@revy review` (`GitHubIndexJobTriggerSource.command`) and admin manual index **bypass** coalesce.
- Revision row created **immediately** on synchronize (`create_revision=True` unchanged).
- Resolution pairing (`apply_resolution_for_synchronize`) is a **separate** async task — coalesce debounces only `maybe_enqueue_pipeline_for_revision`, not resolution (RG-15).
- New Celery task `schedule_autostart_pipeline_for_revision` with `apply_async(countdown=review_coalesce_seconds, kwargs={revision_id, token})`.
- Token = `revision_id` string; at fire time re-check `is_authoritative_for_pull_request_head` — stale task **no-ops** (v1 cancel mechanism).
- **v1:** no `celery_task_id` column on revision; no Redis — each synchronize schedules a new delayed task; only the task whose `revision_id` is still authoritative enqueues.
- Cap enforced in settings validator (P0) — max 10.

## Out of scope for P4

- Redis debounce store (Celery-only v1)
- Coalesce on command path

---

## P4.1 — Debounced scheduler task

**What:** Add `schedule_autostart_pipeline_for_revision` in `github_tasks.py` (or `review_pipeline.py`): at fire time, if `is_authoritative_for_pull_request_head` and coalesce still desired → `maybe_enqueue_pipeline_for_revision(..., trigger=autostart)`.

**Files:** `backend/app/workers/github_tasks.py`, `backend/app/services/review_pipeline.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/workers/github_tasks.py app/services/review_pipeline.py
```

---

## P4.2 — Wire synchronize webhook path

**What:** Replace direct `maybe_enqueue_pipeline_for_revision` in `process_github_event` for autostart synchronize with: if `review_coalesce_seconds == 0` → enqueue immediately (current behavior); else `schedule_autostart_pipeline_for_revision.delay(...)`.

**Files:** `backend/app/workers/github_tasks.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_tasks_autostart.py -k "coalesce" -q
```

---

## P4.3 — Coalesce unit tests

**What:** Tests:

1. `review_coalesce_seconds=0` — synchronize enqueues index immediately (mock `maybe_enqueue_pipeline_for_revision` called once).
2. `review_coalesce_seconds=5` — first sync schedules countdown; second sync within window reschedules; only one pipeline enqueue after authority check.
3. Stale task fires after newer revision — `maybe_enqueue` not called.

**Files:** `backend/tests/unit/test_github_tasks_autostart.py`, `backend/tests/unit/test_github_generation_lifecycle.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_tasks_autostart.py tests/unit/test_github_generation_lifecycle.py -k "coalesce" -q
```

---

## P4.4 — Command bypass test

**What:** `@revy review` / `command` trigger still calls `maybe_enqueue_pipeline_for_revision` immediately when coalesce > 0.

**Files:** `backend/tests/unit/test_github_tasks_autostart.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_tasks_autostart.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check .
pipenv run pytest tests/unit/test_github_tasks_autostart.py tests/unit/test_github_generation_lifecycle.py -k "coalesce or autostart" -q
```

**Next:** [REVIEW_GENERATION_LIFECYCLE_P5_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P5_EXECUTION.md)
