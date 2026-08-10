# Pipeline observability P1 — LLM instrumentation (execution)

Phase **P1** of [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](../PIPELINE_OBSERVABILITY_GENERAL_PLAN.md). Baseline: findings §Catalog — instrumentation by stage. **P1 only.**

**Goal:** Moonshot (review + publish), Anthropic judge, and pipeline-triggered Voyage embeds write attempt rows with tokens/`finish_reason` and unified `llm_call_*` logs.

## Decisions locked for P1

- **Extend P0.5 wiring** in `github_review._call_llm` — add success-path `complete_attempt` with Moonshot `usage` + `finish_reason`; do not add a second recorder hook.
- `moonshot_review._complete_chat` gains optional kwargs: `recorder`, `pipeline_run_id`, `review_run_id`, `step_type`, `attempt_no`.
- Publish path: `github_publish.py` → `github_publish_formatter.complete_issue_comment_markdown` → `_complete_chat` with `step_type=publish`.
- Anthropic judge: instrument `anthropic_review` judge completion path (not `bedrock_review.py` — PO-Q13 deferred).
- Voyage: resolve `pipeline_run_id` via `get_pipeline_run_for_index_job(session, index_job_id=job.id)` inside embed path in `github_indexing.py`; skip attempt row when None (PO-Q16).
- Dual-emit: `llm_call_*` + alias `judge_llm_*` when `step_type=judge` (PO-Q9).
- Pipeline step token columns summed from attempts at step record time.
- **PO-V2 in P1:** in-memory `compute_token_rollup_from_attempts()` helper + tests only; persisting `run.token_rollup` → **P3**.

## Out of scope for P1

- Bedrock `bedrock_review.py` → follow-on (PO-Q13)
- `processing` pipeline steps → **P2**
- Persist `token_rollup` / `estimated_usd` on review run → **P3**
- Manual-index Voyage calls without `pipeline_run_id`

---

## P1.1 — Moonshot `_complete_chat` recorder wiring

**What:** Parse Moonshot `usage` + `finish_reason`; extend P0.5 `_call_llm` recorder path for success + failure. Review path only in this subphase.

**Files:** `backend/app/integrations/moonshot_review.py`, `backend/app/services/github_review.py`, `backend/tests/unit/test_moonshot_review_observability.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_moonshot_review_observability.py -q
```

---

## P1.2 — Publish formatter Moonshot path

**What:** Pass recorder context from `github_publish.py` (~1657) through `github_publish_formatter` → `_complete_chat` with `step_type=publish`.

**Files:** `backend/app/services/github_publish.py`, `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_publish_formatter_observability.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_publish_formatter_observability.py -q
```

---

## P1.3 — Anthropic judge instrumentation + log dual-emit

**What:** Attempt row per judge candidate; map usage tokens; emit `llm_call_*` + alias `judge_llm_*` with unified `failure_class`.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/app/services/github_finding_judge.py`, `backend/tests/unit/test_anthropic_review_observability.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review_observability.py -q
```

---

## P1.4 — Voyage embeddings (pipeline-trigger only)

**What:** In `github_indexing` embed batch path, call `get_pipeline_run_for_index_job(session, index_job_id=job.id)`; when present, pass `pipeline_run_id` to `voyage_embeddings` recorder. Write `index_embed` rows with null tokens and `batch_size`; skip when no pipeline run.

**Files:** `backend/app/integrations/voyage_embeddings.py`, `backend/app/services/github_indexing.py`, `backend/tests/unit/test_voyage_embeddings_observability.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_voyage_embeddings_observability.py -q
```

---

## P1.5 — Pipeline step token rollups + PO-V1/V2 (in-memory)

**What:** `record_review_pipeline_step`, `record_judge_pipeline_step`, `record_publish_pipeline_step` set `input_tokens`/`output_tokens` from attempt sums. PO-V1: mocked run has Moonshot review + publish attempt rows with tokens. PO-V2: in-memory rollup helper equals sum of attempts (**persist in P3**).

**Files:** `backend/app/services/github_pipeline_trace.py`, `backend/app/services/llm_call_recorder.py`, `backend/tests/unit/test_pipeline_observability_po_v1_v2.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_pipeline_observability_po_v1_v2.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/integrations/moonshot_review.py app/integrations/anthropic_review.py app/integrations/voyage_embeddings.py app/services/github_publish.py app/services/github_publish_formatter.py app/services/github_indexing.py app/services/github_pipeline_trace.py
pipenv run pytest tests/unit/test_moonshot_review_observability.py tests/unit/test_publish_formatter_observability.py tests/unit/test_anthropic_review_observability.py tests/unit/test_voyage_embeddings_observability.py tests/unit/test_pipeline_observability_po_v1_v2.py -q
```

**Next:** [PIPELINE_OBSERVABILITY_P2_EXECUTION.md](./PIPELINE_OBSERVABILITY_P2_EXECUTION.md)
