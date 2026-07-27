# Review generation lifecycle P2 — Supersede + stage-entry guards (execution)

Phase **P2** of [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](./REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md). Baseline: findings RG-2, RG-7, RG-8, RG-11, RG-Q8, RG-Q11. **P2 only.**

**Goal:** New `synchronize` supersedes prior generations; authority at index/review/publish entry; stale G10 checks finalized at supersede moment.

## Decisions locked for P2

- On `synchronize` after revision create: `mark_review_runs_superseded_for_pull_request(keep_revision_id=new_revision.id)` + finalize G10 neutral for each superseded in-flight pipeline linked to those review runs.
- `index_pull_request_revision`: before `start_pipeline_github_check`, if not `is_authoritative_for_pull_request_head` → skip G10 + `ensure_pipeline_run_for_index_job` / stash (index `run_index_job` may still execute — RG-Q11).
- `prepare_review_after_index`: if not authoritative → return `ReviewAfterIndexOutcome()` without `create_review_run`.
- `reconcile_tasks.py`: after reconcile, if review run `superseded` → skip `enqueue_publish_for_review_run`.
- `@revy review` on same PR: on **command** enqueue (`issue_comment` path), call `mark_pending_review_runs_superseded_for_revision` for current HEAD revision before `maybe_enqueue_pipeline_for_revision` (supersedes autostart in-flight on same revision).
- PRODUCT_PATTERNS generation row → **in flight** (link to this program).

## Out of scope for P2

- Full surface flush → **P3**
- Coalesce debounce → **P4**
- Judge filter → **P5**

---

## P2.1 — Supersede hook on synchronize

**What:** In `apply_pull_request_webhook_event` synchronize path (after `new_revision` flush) or `github_tasks` before enqueue: call `mark_review_runs_superseded_for_pull_request`; for each returned superseded review run, load pipeline run and `finalize_pipeline_github_check_neutral`.

**Files:** `backend/app/services/github_pull_requests.py` and/or `backend/app/workers/github_tasks.py`, `backend/app/services/github_generation_lifecycle.py`, `backend/app/services/github_pipeline_trace.py`

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

**What:** In `process_github_event` `issue_comment` path, before `maybe_enqueue_pipeline_for_revision` with `trigger=command`: call `mark_pending_review_runs_superseded_for_revision(session, revision_id=…)` so `@revy review` wins over autostart on same HEAD.

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

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check .
pipenv run pytest tests/unit/test_github_generation_lifecycle.py tests/unit/test_index_tasks_generation.py tests/unit/test_review_pipeline.py tests/unit/test_reconcile_tasks_generation.py tests/unit/test_github_tasks_autostart.py -k "not_authoritative or prepare_review_after_index or supersede or command_supersedes" -q
```

**Next:** [REVIEW_GENERATION_LIFECYCLE_P3_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P3_EXECUTION.md)
