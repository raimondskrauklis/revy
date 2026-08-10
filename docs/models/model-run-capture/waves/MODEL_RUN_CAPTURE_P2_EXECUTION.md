# docs/models/model-run-capture/waves/MODEL_RUN_CAPTURE_P2_EXECUTION.md

# MRC-P2 — Pipeline models snapshot + staging metrics (execution)

Phase **MRC-P2** of [`MODEL_RUN_CAPTURE_GENERAL_PLAN.md`](../MODEL_RUN_CAPTURE_GENERAL_PLAN.md). Baseline: findings MRC-Q4, MRC-Q9. **MRC-P2 only.**

**Goal:** `github_pipeline_runs.models_snapshot` JSONB summarizes embedding, reviewer, judge, publish models; staging script groups by `step_type` + model.

## Decisions locked for MRC-P2

- Snapshot shape: `{ "embedding": {provider, model_id, dimensions?}, "reviewer": {...}, "judge": {...}, "publish": {...} }` — null keys when stage did not run.
- **Terminal writer only** (MRC-Q9): populate once at pipeline terminal — publish success, check `failure`, or check `neutral` (partial snapshot of completed stages only); not incremental per stage in v1.
- Rollup sources: index step manifest + review/judge/publish step `model_*` fields + attempt rows as fallback.
- Staging metrics: `GROUP BY step_type, provider, request_model` on `github_llm_call_attempts`.
- MRC-Q7 (`query_embedding_model` on retrieve manifest) → **out of scope** (v1.1).

## Out of scope for MRC-P2

- API response exposure → **MRC-P3**
- `estimated_usd` by model → PO-P3
- Cross-model mismatch alerts → parking lot

---

## MRC-P2.1 — Migration `models_snapshot` on pipeline runs

**What:** Hand-written Alembic revision adds nullable JSONB `models_snapshot` to `github_pipeline_runs`. **LOOP pauses after this subphase** until `alembic upgrade head` on staging.

**Files:** `backend/alembic/versions/` (`down_revision = "2026_08_10_1200_0031_pipeline_observability"`), `backend/app/models/github_pipeline.py`

**Deliverable:** Migration applies cleanly; schema test passes.

```bash
cd backend && pipenv run pytest tests/unit/test_pipeline_observability_schema.py -q
```

---

## MRC-P2.2 — `build_models_snapshot` helper

**What:** Pure function (or service helper) builds snapshot dict from pipeline steps + attempts for a run id. Maps `index` step manifest → `embedding`; `review` → `reviewer`; `judge` → `judge`; `publish` → `publish`.

**Files:** `backend/app/services/model_run_snapshot.py` (new), `backend/tests/unit/test_model_run_snapshot.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_model_run_snapshot.py -q
```

---

## MRC-P2.3 — Terminal snapshot writer hooks

**What:** Add `persist_models_snapshot(session, *, pipeline_run_id)` that calls `build_models_snapshot` and writes `github_pipeline_runs.models_snapshot`. Hook in **two places** only (avoids missing a worker path):

1. **Success:** end of `record_publish_pipeline_step` (or immediately after in `run_publish_job` when `pipeline_run_id` known) — judge step already exists from `reconcile_tasks`; publish is last stage.
2. **Terminal check finalize (failure + neutral + partial):** inside `_finalize_pipeline_github_check` in `github_pipeline_trace.py` — covers `finalize_pipeline_github_check_failure`, `finalize_pipeline_github_check_neutral`, and wrappers `finalize_pipeline_github_check_for_index_job`, `finalize_pipeline_github_check_for_review_run`, `finalize_pipeline_github_check_for_publish_job` (call sites in `index_tasks.py`, `review_tasks.py`, `publish_tasks.py`, `reconcile_tasks.py`, `github_publish.py`).

Do **not** write snapshot in `reconcile_tasks` on success (publish is async). Partial runs include only stages with completed steps / manifest data.

**Files:** `backend/app/services/model_run_snapshot.py`, `backend/app/services/github_pipeline_trace.py`, `backend/app/services/github_publish.py`, `backend/tests/unit/test_model_run_snapshot.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_model_run_snapshot.py -k "terminal or finalize" -q
```

---

## MRC-P2.4 — Staging metrics model breakdown

**What:** Extend `pipeline_observability_staging_metrics.py` with query `GROUP BY step_type, provider, request_model`; include in `--json` output as `model_breakdown`.

**Files:** `backend/scripts/pipeline_observability_staging_metrics.py`, `backend/tests/unit/test_pipeline_observability_staging_metrics.py` (add if missing)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_pipeline_observability_staging_metrics.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/services/model_run_snapshot.py app/services/github_pipeline_trace.py app/models/github_pipeline.py
pipenv run pytest tests/unit/test_model_run_snapshot.py tests/unit/test_pipeline_observability_schema.py -q
```

**Deploy:** Run `alembic upgrade head` before worker deploy.

**Next:** [`MODEL_RUN_CAPTURE_P3_EXECUTION.md`](./MODEL_RUN_CAPTURE_P3_EXECUTION.md)
