# Pipeline observability P0 — foundations (execution)

**Status:** **shipped** on `main` ([#92](https://github.com/raimondskrauklis/revy/pull/92), `be16bc7`).

Phase **P0** of [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](../PIPELINE_OBSERVABILITY_GENERAL_PLAN.md). Baseline: [PIPELINE_OBSERVABILITY_FINDINGS.md](../PIPELINE_OBSERVABILITY_FINDINGS.md) §Commit graph, §Metric catalog. **P0 only.**

**Goal:** Schema + `LlmCallRecorder` + durable checkpoint/`_mark_failed` commits survive Celery retries; PO-V3 HTTP-timeout case passes without success-path tokens.

## Decisions locked for P0

- Migration `0031` — hand-written Alembic only; **LOOP pauses** after migration subphase.
- `github_llm_call_attempts`: `pipeline_run_id` NOT NULL when row inserted; `review_run_id` nullable; `batch_size` nullable (Voyage embed); `failure_class` nullable on success.
- `GitHubReviewRunFailureClass` enum in `enums.py` — values per findings §Terminology.
- `llm_pricing`: static config module `backend/app/core/llm_pricing.py` (placeholder rates OK) — no `estimated_usd` computation until P3.
- **Recorder session strategy (PO-Q17):** boundaries **#2–#3** (attempt start/complete/fail) use a **dedicated** `async with get_db_context()` per call — never `commit()` on the worker’s shared review session. Boundary **#1** checkpoint uses the shared `run_review_run` session, then `await session.refresh(run)` after `commit()`. Boundary **#6** `_mark_failed` uses its own short-lived session when main txn never committed.
- `trigger_source` on review runs: reuse `GitHubIndexJobTriggerSource` enum; copied in `create_review_run` from `get_latest_completed_index_job` (PO-Q15).
- Judge legacy log map: `parse`/`empty_body` → `parse_error`; `http` → `provider_error`.
- PO-V3 tests mock HTTP timeout — not SoftTimeLimitExceeded.

## PR review context (first commit)

- **SSOT:** `.revy/review-context.json` — `active_program: pipeline-observability`; P1 execution path (post-P0 ship).
- **Greptile:** `cd backend && python -m scripts.generate_greptile_files_from_review_context --write`
- **Bugbot:** `.cursor/BUGBOT.md` — pipeline-observability program links.

## Out of scope for P0

- Success-path token capture on LLM calls → **P1** (extends P0.5 timeout wiring in `_call_llm`)
- `processing` pipeline steps → **P2**
- `estimated_usd` computation → **P3**
- `revy_revision_llm_http_timeout_seconds` → shipped PR #90

---

## P0.0 — Program PR review context

**What:** Switch review-context SSOT; regenerate Greptile files; update Bugbot program block.

**Files:** `.revy/review-context.json`, `.agent/review-context.json` (mirror), `.cursor/BUGBOT.md`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_generate_greptile_files.py -q
cd backend && python -m scripts.generate_greptile_files_from_review_context --check
```

---

## P0.1 — Alembic schema migration

**What:** Add `github_llm_call_attempts` table; extend `github_review_runs` with `timing_stats`, `token_rollup`, `failure_stage`, `failure_class`, `trigger_source` (enum); FK attempts → `github_pipeline_runs` ON DELETE CASCADE.

**Files:** `backend/alembic/versions/2026_08_10_1200_0031_pipeline_observability.py`, `backend/app/models/github_llm_call_attempt.py`, `backend/app/models/github_review_run.py`, `backend/app/constants/enums.py`, `backend/app/models/__init__.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_pipeline_observability_schema.py -q
```

**LOOP pause:** apply migration on staging before P0.2+ code depends on columns.

---

## P0.2 — `llm_pricing` config (structure only)

**What:** Static price map skeleton for Moonshot, Anthropic judge, Voyage — used in P3 only. `lookup_price(provider, model_id) -> LlmPrice | None`.

**Files:** `backend/app/core/llm_pricing.py`, `backend/tests/unit/test_llm_pricing.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_llm_pricing.py -q
```

---

## P0.3 — `LlmCallRecorder` + failure taxonomy helpers

**What:** `start_attempt`, `complete_attempt`, `fail_attempt` — each opens **dedicated** `get_db_context()`, writes, commits, closes. Helpers: `classify_failure_class(exc) -> GitHubReviewRunFailureClass`. No HTTP instrumentation yet.

**Files:** `backend/app/services/llm_call_recorder.py`, `backend/app/services/observability_failure.py`, `backend/tests/unit/test_llm_call_recorder.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_llm_call_recorder.py -q
```

---

## P0.4 — Checkpoint commit + `trigger_source` + purge extension

**What:** After retrieve in `run_review_run`, boundary **#1** commits on shared session: `context_stats`, `provider`, `model_id`, partial `timing_stats` (`compare_ms`, `supplemental_ms`), `failure_stage=retrieve`; then `await session.refresh(run)`. Set `trigger_source` in `create_review_run`. Extend `purge_old_pipeline_artifacts` to cascade-delete attempts.

**Files:** `backend/app/services/github_review.py`, `backend/app/services/github_pipeline_trace.py`, `backend/tests/unit/test_github_review_observability_checkpoint.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review_observability_checkpoint.py -q
```

---

## P0.5 — `_mark_failed` enrichment + PO-V3 timeout durability

**What:** `review_tasks._mark_failed` writes `failure_stage`/`failure_class` via boundary **#6** (dedicated session). Wire recorder around review LLM for timeout-only path in `_call_llm`: on `httpx.TimeoutException`, `fail_attempt(failure_class=timeout)` before Celery retry. **P1.1 extends this wiring** for success-path tokens — do not duplicate hooks.

**Files:** `backend/app/workers/review_tasks.py`, `backend/app/services/github_review.py`, `backend/tests/unit/test_review_observability_po_v3.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_review_observability_po_v3.py tests/unit/test_llm_call_recorder.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/services/llm_call_recorder.py app/services/observability_failure.py app/services/github_review.py app/workers/review_tasks.py app/core/llm_pricing.py
pipenv run pytest tests/unit/test_pipeline_observability_schema.py tests/unit/test_llm_pricing.py tests/unit/test_llm_call_recorder.py tests/unit/test_github_review_observability_checkpoint.py tests/unit/test_review_observability_po_v3.py tests/unit/test_generate_greptile_files.py -q
```

**Human gate (non-blocking):** Operator applies migration `0031` on staging before P1.

**Next:** [PIPELINE_OBSERVABILITY_P1_EXECUTION.md](./PIPELINE_OBSERVABILITY_P1_EXECUTION.md)
