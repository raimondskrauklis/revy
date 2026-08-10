# docs/models/model-run-capture/waves/MODEL_RUN_CAPTURE_P0_EXECUTION.md

# MRC-P0 — Index embedding identity (execution)

Phase **MRC-P0** of [`MODEL_RUN_CAPTURE_GENERAL_PLAN.md`](../MODEL_RUN_CAPTURE_GENERAL_PLAN.md). Baseline: [`MODEL_RUN_CAPTURE_FINDINGS.md`](../MODEL_RUN_CAPTURE_FINDINGS.md) §Target catalog, MRC-Q8. **MRC-P0 only.**

**Goal:** Pipeline-triggered index jobs persist Voyage embedding model + dimensions on the index step manifest and step row when embed HTTP runs.

## Decisions locked for MRC-P0

- Capture `embedding_provider`, `embedding_model`, `embedding_dimensions` in `github_indexing` at embed batch time — extend `_set_index_manifest_stats`.
- `record_index_pipeline_step` copies from `job.index_manifest_stats` only — **no** `settings.revy_embedding_model` read in trace writer.
- Index step `model_provider` = `voyage`; `model_id` = captured `embedding_model`.
- Update **both** create and update paths when index step already exists (`pending` from `stash_pipeline_github_check_run_id`).
- When `embed_batches=0`: **`record_index_pipeline_step`** (not `_set_index_manifest_stats`) sets `embedding_skipped_reason=reused_chunks_only`; omit or null `embedding_model` / `embedding_dimensions`; leave index step `model_provider`/`model_id` null (MRC-Q8).

## Out of scope for MRC-P0 (later phases)

- `github_llm_call_attempts` → **MRC-P1**
- Per-chunk `embedding_model` column → deferred
- Manual-index jobs without pipeline run → **MRC-Q6**

---

## MRC-P0.1 — Capture embedding model at embed HTTP time

**What:** When `embed_texts` runs in `github_indexing` (single call site per job today — `github_indexing.py` ~598), record provider `voyage`, `settings.revy_embedding_model`, and `settings.revy_embedding_dimensions` into `index_manifest_stats` on first embed only; do **not** set `embedding_skipped_reason` here.

**Files:** `backend/app/services/github_indexing.py`

**Deliverable:** Unit test asserts `index_manifest_stats` contains embedding fields after index with new chunks.

```bash
cd backend && pipenv run pytest tests/unit/test_github_indexing.py -k "manifest_stats or embedding_model" -q
```

---

## MRC-P0.2 — Persist manifest + index step model columns

**What:** `record_index_pipeline_step` merges embedding keys from `job.index_manifest_stats` into manifest artifact. When `embed_batches == 0` in stats: set manifest `embedding_skipped_reason=reused_chunks_only`; do not copy `embedding_*` keys; leave `step.model_provider` / `step.model_id` null. When embed ran: set `step.model_provider=voyage`, `step.model_id=embedding_model`. Apply on **both** create and update paths for pre-existing `pending` index step.

**Files:** `backend/app/services/github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py -k "record_index_pipeline_step" -q
```

---

## MRC-P0.3 — Reuse-only index null semantics

**What:** Test path where all chunks reused (`embed_batches=0`) — manifest has `embedding_skipped_reason=reused_chunks_only` and no false `embedding_model` from current env.

**Files:** `backend/tests/unit/test_github_indexing.py`, `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_indexing.py tests/unit/test_github_pipeline_trace.py -k "reused_chunks or embed_batches" -q
```

---

## MRC-P0.4 — Pending index step update path

**What:** Test that `record_index_pipeline_step` after `stash_pipeline_github_check_run_id` updates model fields on pre-existing `pending` index step (not only `_create_completed_step`).

**Files:** `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py -k "pending or stash_pipeline" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/services/github_indexing.py app/services/github_pipeline_trace.py
pipenv run pytest tests/unit/test_github_indexing.py tests/unit/test_github_pipeline_trace.py -q
```

**Deploy:** Backend + worker only; no migration.

**Next:** [`MODEL_RUN_CAPTURE_P1_EXECUTION.md`](./MODEL_RUN_CAPTURE_P1_EXECUTION.md)
