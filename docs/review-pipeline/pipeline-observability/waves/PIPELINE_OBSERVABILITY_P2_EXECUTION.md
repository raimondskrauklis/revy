# Pipeline observability P2 — incremental pipeline trace (execution)

Phase **P2** of [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](../PIPELINE_OBSERVABILITY_GENERAL_PLAN.md). Baseline: findings §Metric catalog §4. **P2 only.**

**Goal:** Live `processing` → terminal pipeline steps for retrieve/review (and reconcile/judge/publish where applicable); abort paths show stage progress without re-writing existing end-of-task terminal steps on clean `_run` failures.

## Decisions locked for P2

- New helpers: `begin_pipeline_step`, `finish_pipeline_step` in `github_pipeline_trace.py` — use `PipelineStepStatus.processing`.
- Write `retrieve` step before review LLM; `review` step enters `processing` before `_call_llm`, terminal on return/fail.
- Retrieve **manifest** gains `retrieval.results_count`, `retrieval.empty`, `context.truncated` (OTel RAG names). **`context_stats` copy** of retrieval counts → **P3.3** (intentional split: artifact vs run summary).
- `timing_stats` sub-phases: `compare_ms`, `supplemental_ms` at checkpoint (boundary #1).
- Do not duplicate terminal steps already written at end of successful `_run`.

## Out of scope for P2

- GitHub API sub-spans
- `review_llm_wait_ms` finalize → **P3.2**
- `estimated_usd` → **P3**

---

## P2.1 — `processing` → terminal trace API

**What:** `begin_pipeline_step` inserts/updates step to `processing` with `started_at`; `finish_pipeline_step` sets `completed`/`failed`, `duration_ms`, `error`.

**Files:** `backend/app/services/github_pipeline_trace.py`, `backend/tests/unit/test_pipeline_trace_processing.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_pipeline_trace_processing.py -q
```

---

## P2.2 — Retrieve + review incremental steps

**What:** In `run_review_run`, `begin_pipeline_step(retrieve)` before retrieve work; `finish_pipeline_step` after retrieve. Before review LLM: `begin_pipeline_step(review)`; finish on success or parse-fail path.

**Files:** `backend/app/services/github_review.py`, `backend/tests/unit/test_github_review_pipeline_steps.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review_pipeline_steps.py -q
```

---

## P2.3 — Retrieve manifest + sub-phase timing

**What:** Extend retrieve manifest/recording with `retrieval.*` attrs; merge `compare_ms`/`supplemental_ms` into `timing_stats` at checkpoint.

**Files:** `backend/app/services/github_review.py`, `backend/app/services/github_pipeline_trace.py`, `backend/tests/unit/test_retrieve_manifest_observability.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_retrieve_manifest_observability.py -q
```

---

## P2.4 — Reconcile/judge/publish incremental updates

**What:** Wire `begin`/`finish` for reconcile/judge in `reconcile_tasks.py` + `github_finding_judge.py`. Publish LLM + `record_publish_pipeline_step` in **`github_publish.py`** (~2178) — not `publish_tasks.py` alone.

**Files:** `backend/app/workers/reconcile_tasks.py`, `backend/app/services/github_finding_judge.py`, `backend/app/services/github_publish.py`, `backend/tests/unit/test_pipeline_steps_workers.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_pipeline_steps_workers.py -q
```

---

## P2.5 — PO-V6 truncation path

**What:** When Moonshot returns `finish_reason=length`, review step `failed`, `failure_class=truncated` on run (if not already set in P0/P1).

**Files:** `backend/app/integrations/moonshot_review.py`, `backend/tests/unit/test_pipeline_observability_po_v6.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_pipeline_observability_po_v6.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/services/github_pipeline_trace.py app/services/github_review.py app/services/github_publish.py
pipenv run pytest tests/unit/test_pipeline_trace_processing.py tests/unit/test_github_review_pipeline_steps.py tests/unit/test_retrieve_manifest_observability.py tests/unit/test_pipeline_steps_workers.py tests/unit/test_pipeline_observability_po_v6.py -q
```

**Next:** [PIPELINE_OBSERVABILITY_P3_EXECUTION.md](./PIPELINE_OBSERVABILITY_P3_EXECUTION.md)
