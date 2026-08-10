# Pipeline observability P3 — rollups & API (execution)

Phase **P3** of [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](../PIPELINE_OBSERVABILITY_GENERAL_PLAN.md). Baseline: findings §Metric catalog §2–3, PO-V2. **P3 only.**

**Goal:** `timing_stats` + `token_rollup` finalized on all terminal paths; API exposes rollups and `model_id`. Optional `estimated_usd` (low priority).

## Decisions locked for P3

- `stats_version: 1` on `timing_stats` and `token_rollup` JSONB.
- **`timing_stats` keys (PO-Q18):** `index_ms`, `retrieve_ms`, `compare_ms`, `supplemental_ms`, **`review_llm_wait_ms`** (from `ReviewRunOutcome.review_duration_ms`), `reconcile_ms`, `judge_ms`, `publish_ms`.
- **PO-V4 latency SSOT:** primary = `github_llm_call_attempts.wait_ms` where `step_type=review`; `timing_stats.review_llm_wait_ms` is run-level mirror for API/scripts.
- `token_rollup`: persist to `run.token_rollup` from P1 rollup helper; by provider/model breakdown.
- `estimated_usd` = Σ(tokens × `llm_pricing`) when tokens present — **optional output**, not a gate (money tracking deferred to PO-Q12 vendor APIs).
- Partial rollups when only subset of stages completed; `_mark_failed` writes partial state if checkpoint ran.
- `GitHubReviewRunResponse` adds: `model_id`, `timing_stats`, `token_rollup`, `failure_stage`, `failure_class`, `trigger_source`.
- P3.3 `context_stats` retrieval fields duplicate P2.3 manifest by design (run summary vs artifact).

## Out of scope for P3

- Staging metrics script → **P4**
- Vendor billing API reconcile (PO-Q12)
- Frontend UI charts

---

## P3.1 — Rollup computation service

**What:** `compute_token_rollup(review_run_id) -> dict` sums attempts by provider/model; `compute_estimated_usd(rollup) -> Decimal | None` (returns None when any token null).

**Files:** `backend/app/services/review_run_rollups.py`, `backend/tests/unit/test_review_run_rollups.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_review_run_rollups.py -q
```

---

## P3.2 — Finalize `timing_stats` + persist `token_rollup`

**What:** At end of `run_review_run` and worker terminal paths, persist full `timing_stats` including **`review_llm_wait_ms`** from `review_duration_ms`; commit `token_rollup`. PO-V2 regression.

**Files:** `backend/app/services/github_review.py`, `backend/app/workers/review_tasks.py`, `backend/tests/unit/test_review_run_rollups.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_review_run_rollups.py tests/unit/test_pipeline_observability_po_v1_v2.py -q
```

---

## P3.3 — `context_stats` retrieval enrichment

**What:** At retrieve finalize, merge `retrieval.results_count` and `supplemental.hit_count` into `context_stats` (mirrors P2.3 manifest).

**Files:** `backend/app/services/github_review.py`, `backend/app/services/engineering_context/stats.py`, `backend/tests/unit/test_context_stats_retrieval.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_context_stats_retrieval.py -q
```

---

## P3.4 — API schema exposure

**What:** Extend `GitHubReviewRunResponse` + `installation_review.py` mapping for observability fields; include ORM `model_id`.

**Files:** `backend/app/schemas/github_review.py`, `backend/app/api/v1/workspaces/installation_review.py`, `backend/tests/unit/test_github_review_api_observability.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review_api_observability.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/services/review_run_rollups.py app/schemas/github_review.py
pipenv run pytest tests/unit/test_review_run_rollups.py tests/unit/test_context_stats_retrieval.py tests/unit/test_github_review_api_observability.py tests/unit/test_pipeline_observability_po_v1_v2.py -q
```

**Next:** [PIPELINE_OBSERVABILITY_P4_EXECUTION.md](./PIPELINE_OBSERVABILITY_P4_EXECUTION.md)
