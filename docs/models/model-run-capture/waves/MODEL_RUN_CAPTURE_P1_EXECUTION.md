# docs/models/model-run-capture/waves/MODEL_RUN_CAPTURE_P1_EXECUTION.md

# MRC-P1 — LLM attempt rows + judge/publish step models (execution)

Phase **MRC-P1** of [`MODEL_RUN_CAPTURE_GENERAL_PLAN.md`](../MODEL_RUN_CAPTURE_GENERAL_PLAN.md). Baseline: findings §Target catalog, MRC-Q10. **MRC-P1 only.**

**Goal:** Every LLM HTTP stage writes `request_model` on attempt rows; judge and publish pipeline steps expose `model_provider`/`model_id`.

## Decisions locked for MRC-P1

- **Voyage `index_embed`:** Implement [PO-P1.4](../../review-pipeline/pipeline-observability/waves/PIPELINE_OBSERVABILITY_P1_EXECUTION.md) contract if not on `main` — `get_pipeline_run_for_index_job`; skip when no `pipeline_run_id`; `batch_size`; null tokens OK.
- Pass captured `embedding_model` from `index_manifest_stats` into recorder `request_model` (not a second `settings` read in `voyage_embeddings`).
- `request_model` on embed attempts **must match** index manifest `embedding_model` from MRC-P0.
- Judge step: `record_review_run_judge_status` returns resolved `ModelRef | None`; `reconcile_tasks` passes `model_provider`/`model_id` into `record_judge_pipeline_step`. When judge skipped (disabled/unavailable), `model_ref=None` — step row omits model fields.
- Publish step: set `model_provider`/`model_id` from formatter `ModelRef` when publish LLM runs — **requires PO-P1.2 on `main` or equivalent recorder wiring in P1.4** (human gate).
- Review path: regression-only unless gaps found — `start_attempt` already wired in `github_review.py`.

## Out of scope for MRC-P1

- Token rollup persistence → PO-P3
- `models_snapshot` column → **MRC-P2**
- Manual-index embed attempts → MRC-Q6
- Bedrock-specific paths → defer

---

## MRC-P1.1 — Voyage `index_embed` attempt rows

**What:** Wire embed batch path with `LlmCallRecorder`; `step_type=index_embed`, `operation_name=embeddings`, `provider=voyage`, `index_job_id`, `batch_size`. In `github_indexing`, pass `request_model` from captured `index_manifest_stats["embedding_model"]` into `embed_texts` / recorder kwargs (single source with MRC-P0 manifest). Idempotent if PO-P1.4 already landed — extend rather than duplicate.

**Files:** `backend/app/integrations/voyage_embeddings.py`, `backend/app/services/github_indexing.py`, `backend/tests/unit/test_voyage_embeddings_observability.py` (new)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_voyage_embeddings_observability.py -q
```

---

## MRC-P1.2 — Manifest ↔ attempt model parity test

**What:** Unit test: after index with pipeline run, index manifest `embedding_model` equals `github_llm_call_attempts.request_model` for `index_embed` rows.

**Files:** `backend/tests/unit/test_model_run_capture_p1.py` (new)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_model_run_capture_p1.py -k "embed_model_parity" -q
```

---

## MRC-P1.3 — Judge step model fields

**What:**

1. Change `record_review_run_judge_status` return type to `tuple[int, ModelRef | None]` — return `(judged_count, model_ref)` when judge ran, `(0, None)` when skipped/disabled/unavailable.
2. Extend `record_judge_pipeline_step(..., model_provider: str | None = None, model_id: str | None = None)` — pass through to `_create_completed_step`.
3. In `reconcile_tasks`, unpack judge result and call `record_judge_pipeline_step(..., model_provider=model_ref.provider, model_id=model_ref.model_id)` when `model_ref is not None`.

**Files:** `backend/app/services/github_pipeline_trace.py`, `backend/app/workers/reconcile_tasks.py`, `backend/app/services/github_finding_judge.py`, `backend/tests/unit/test_reconcile_tasks.py`, `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py tests/unit/test_reconcile_tasks.py tests/unit/test_github_finding_judge.py -k "judge" -q
```

---

## MRC-P1.4 — Publish step model fields

**Human gate:** Confirm [PO-P1.2](../../review-pipeline/pipeline-observability/waves/PIPELINE_OBSERVABILITY_P1_EXECUTION.md) publish recorder is on `main` before starting this subphase. If not merged, implement PO-P1.2 recorder pass-through in the same PR (do not ship step-only model fields without attempt rows).

**What:** `record_publish_pipeline_step` sets `model_provider`/`model_id` from publish formatter `ModelRef`; attempt rows from publish path include matching `request_model`.

**Files:** `backend/app/services/github_pipeline_trace.py`, `backend/app/services/github_publish.py`, `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_model_run_capture_p1.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_model_run_capture_p1.py -k "publish_model" -q
```

---

## MRC-P1.5 — Review attempt regression

**What:** Confirm review `start_attempt` writes `request_model` matching `review_run.model_id` when pipeline run present; add test if missing.

**Files:** `backend/tests/unit/test_review_observability_po_v3.py` or `backend/tests/unit/test_model_run_capture_p1.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_review_observability_po_v3.py tests/unit/test_model_run_capture_p1.py -k "review_model" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/integrations/voyage_embeddings.py app/services/github_indexing.py app/services/github_pipeline_trace.py app/services/github_finding_judge.py app/workers/reconcile_tasks.py app/services/github_publish.py app/services/github_publish_formatter.py
pipenv run pytest tests/unit/test_voyage_embeddings_observability.py tests/unit/test_model_run_capture_p1.py tests/unit/test_github_pipeline_trace.py tests/unit/test_reconcile_tasks.py tests/unit/test_review_observability_po_v3.py -q
```

**Deploy:** Backend + worker. Prefer single PR with pipeline observability P1 when PO-P1 not yet on `main`; MRC-P1.1 idempotent if PO-P1.4 already shipped.

**Next:** [`MODEL_RUN_CAPTURE_P2_EXECUTION.md`](./MODEL_RUN_CAPTURE_P2_EXECUTION.md)
