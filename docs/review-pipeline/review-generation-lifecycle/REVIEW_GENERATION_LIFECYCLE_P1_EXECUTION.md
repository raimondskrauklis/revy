# Review generation lifecycle P1 — HEAD-gated publish (execution)

Phase **P1** of [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](./REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md). Baseline: findings RG-1, RG-10, RG-12, RG-Q8. **P1 only.**

**Goal:** Stale or superseded generation never writes GitHub surface; same-SHA re-publish works.

## Decisions locked for P1

- `run_publish_job` early exit before any GitHub API when:
  - `job.head_sha != pull_request.head_sha` → `skipped_not_head`
  - linked review run `status == superseded` → `skipped_superseded`
- On skip: persist terminal status; call `finalize_pipeline_github_check_neutral` for linked pipeline (idempotent with P2).
- `find_publish_job_for_head_sha`: **`completed` only** for `is_update_from_other` — terminal skips and in-flight jobs excluded (same-SHA retry creates a new job).
- `create_publish_job_for_review_run`: return `None` when review run is `superseded`.
- Same-SHA admin `POST …/publish` / retry: new publish job allowed when prior job terminal-skipped and revision still HEAD; **`run_publish_job` gate applies** (admin `create_publish_job` does not bypass).
- Skip path: **do not** set `processing` before gate; **do not** call `record_publish_pipeline_step` with `completed` — trace artifact deferred to P5.3.

## Out of scope for P1

- Mark superseded on synchronize → **P2**
- `enqueue_publish_for_review_run` guard → **P2**
- Full surface flush → **P3**

---

## P1.1 — Publish skip gate in `run_publish_job`

**What:** After loading `job`, `run`, `revision`, `pull_request` context — **before** `job.status = processing` — if `job.head_sha != pull_request.head_sha` or review run `superseded`: set terminal skip status (`skipped_not_head` / `skipped_superseded`), skip all GitHub writes, flush session, return job. **Never** flash `processing` on skip paths. Structured log `publish_skipped_not_head` / `publish_skipped_superseded`.

**Files:** `backend/app/services/github_publish.py`, `backend/app/services/github_generation_lifecycle.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "skipped_not_head or skipped_superseded or head_gate" -q
```

---

## P1.2 — Neutral finalize on skip-at-publish

**What:** On P1 skip path, resolve pipeline run for `job.review_run_id`; call `finalize_pipeline_github_check_neutral` with summary `"Superseded by newer commit"` (HEAD mismatch uses same copy — operator-facing).

**Files:** `backend/app/services/github_publish.py`, `backend/app/services/github_pipeline_trace.py`

**Deliverable:** covered by P1.1 tests — assert `finalize_pipeline_github_check_neutral` invoked on skip.

---

## P1.3 — `find_publish_job_for_head_sha` terminal filter

**What:** Add `.where(GitHubPublishJobORM.status == GitHubPublishJobStatus.completed)` (or exclude terminal skips explicitly). Skipped job with copied `github_check_run_id` must not drive `is_update_from_other`.

**Files:** `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "find_publish_job_for_head_sha or skipped_not_head" -q
```

---

## P1.4 — `create_publish_job_for_review_run` superseded guard

**What:** After loading run, if `run.status == superseded` or `is_review_run_superseded(run)`: return `None` without creating job.

**Files:** `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "create_publish_job_for_review_run and superseded" -q
```

---

## P1.5 — Integration-style unit tests

**What:** Harness tests (mock GitHub API):

1. H2 is HEAD — publish for H1 revision → `skipped_not_head`, zero `create_pull_request_review_comment` calls.
2. Review run manually `superseded` — publish task → `skipped_superseded`.
3. Same SHA: prior `skipped_not_head`, still HEAD — new publish job created and can complete.

**Files:** `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "head_gate or skipped_not_head or skipped_superseded" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check .
pipenv run pytest tests/unit/test_github_publish.py -k "head_gate or skipped_not_head or skipped_superseded or find_publish_job_for_head_sha" -q
pipenv run pytest tests/unit/test_github_generation_lifecycle.py -q
```

**Next:** [REVIEW_GENERATION_LIFECYCLE_P2_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P2_EXECUTION.md)
