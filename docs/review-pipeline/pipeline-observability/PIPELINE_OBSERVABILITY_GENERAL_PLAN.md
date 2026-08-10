# Pipeline observability — general plan

**Baseline:** [PIPELINE_OBSERVABILITY_FINDINGS.md](./PIPELINE_OBSERVABILITY_FINDINGS.md) (2026-08-10, post peer-review pass 2)  
**Prerequisite:** HTTP timeout headroom **shipped on `main`** (PR #90) — not a P0 deliverable.

**Thesis:** Full pipeline observability — every stage traced, every LLM call metered, failures typed and **durably checkpointed** across Celery retries. DB is SSOT; field names follow OTel `gen_ai.*`.

**Gap IDs:** **PO-*** in findings; **P0–P5** below.

**Locked:** PO-Q1–Q16 per findings registry.

---

## Cross-cutting (every phase)

- **Commit graph:** explicit `commit()` at checkpoint, attempt start, attempt complete, `_mark_failed` enrichment — not `flush()` alone.
- **Tests:** PO-V3 = HTTP timeout durability + checkpoint only (not success-path tokens).
- **Migrations:** hand-written Alembic; `stats_version` on JSONB; `GitHubReviewRunFailureClass` enum in `enums.py` (P0).
- **Taxonomy:** single `failure_class` enum; map legacy judge log classes in P0.
- **Trace:** P2 adds `processing` → terminal; today writers only create terminal steps end-of-task.
- **Staging:** metrics script + memo when P4 ships.

---

## P0 — Foundations (schema + commit graph + pricing + retention)

**Goal:** Durable run state and attempt rows survive Celery retries, HTTP timeouts, and `_mark_failed`; schema ready for P1 instrumentation.

**Scope — in:**

- Alembic: `github_llm_call_attempts` (`pipeline_run_id` required when row written, `review_run_id` nullable, `index_job_id` nullable, `failure_class`); review-run columns `timing_stats`, `token_rollup`, `failure_stage`, `failure_class`, `trigger_source`.
- `GitHubReviewRunFailureClass` enum in `enums.py`.
- `llm_pricing` config or table — no `estimated_usd` computation yet.
- Extend O8 `purge_old_pipeline_artifacts` to cascade-delete attempts (FK on `pipeline_run_id`).
- `LlmCallRecorder` — start/complete/fail with **per-boundary commit** (timeout path only in P0 tests — no token capture).
- Checkpoint commit after retrieve (boundary #1); `_mark_failed` enrichment commit (boundary #6).
- `trigger_source` set in **`create_review_run`** from `get_latest_completed_index_job` (PO-Q15).
- Map exceptions → `failure_class`; map judge log `parse`/`http`/`empty_body` → taxonomy.

**Scope — out:** Success-path token population (P1); `revy_revision_llm_http_timeout_seconds` (shipped PR #90).

**Deliverables:** Migration + unit tests for commit graph; PO-V3 HTTP-timeout durability case.

**Depends on:** None.

---

## P1 — Unified LLM instrumentation (primary providers)

**Goal:** Moonshot, Anthropic judge, and pipeline-triggered Voyage embed calls write attempt rows + structured logs.

**Scope — in:**

- Instrument `moonshot_review._complete_chat` (review + publish via `github_publish_formatter` — callers pass `step_type` + `pipeline_run_id`).
- Instrument **`anthropic_review`** judge path (staging judge = Anthropic/Claude).
- Instrument **`voyage_embeddings`** for pipeline-trigger index only — skip when no `pipeline_run_id` (PO-Q16); null tokens + batch count (PO-Q11).
- `llm_call_started` / `completed` / `failed` with `failure_class`; dual-emit `judge_llm_*` aliases (PO-Q9).
- Populate pipeline step `input_tokens`/`output_tokens` from attempt sums.

**Scope — out:** TTFT; cache token columns; **`bedrock_review.py`** instrumentation (PO-Q13 — follow-on when Bedrock enabled; recorder contract ready).

**Deliverables:** PO-V1, PO-V2.

**Depends on:** P0.

---

## P2 — Incremental pipeline trace (all stages)

**Goal:** Live progress + abort visibility — not re-inventing terminal steps that already exist on clean `_run` failure paths.

**Scope — in:**

- New trace helpers: create step `processing` → update to `completed`/`failed`.
- Write `retrieve` before review LLM; `review` step during LLM wait.
- Retrieve manifest `retrieval.*` attrs; sub-phase timing in `timing_stats`.

**Scope — out:** GitHub API sub-spans.

**Deliverables:** Failed abort run shows `retrieve` + `review` steps; PO-V6.

**Depends on:** P0.

---

## P3 — Run-level rollups & context enrichment

**Goal:** One glance at `github_review_runs` answers size, cost, and where time went.

**Scope — in:**

- Finalize `timing_stats` + `token_rollup` + `estimated_usd` (from P0 `llm_pricing`) on completion, in-run failure, and `_mark_failed`.
- Partial rollups when only some attempts exist.
- Extend `context_stats` with retrieval counts.
- API: expose rollups + existing ORM `model_id` on `GitHubReviewRunResponse`.

**Scope — out:** UI charts; vendor billing (PO-Q12).

**Deliverables:** Dogfood PR row shows token totals and timing breakdown.

**Depends on:** P1–P2.

---

## P4 — Staging metrics & SLO reports

**Goal:** Operator script for tokens, latency percentiles, failure taxonomy, truncation — primary sign-off.

**Scope — in:**

- `pipeline_observability_staging_metrics.py` — percentiles from `attempts.wait_ms`, taxonomy, truncation, token totals; `--po-gate`.
- Optional `--show-estimated-cost` (off by default).

**Scope — out:** CSV reconcile; vendor account APIs (PO-Q12); CI enforcement.

**Deliverables:** PO-V4; [staging-validation](../staging-validation/README.md) index row.

**Depends on:** P3.

---

## P5 — OTel OTLP export (optional)

**Goal:** Vendor-neutral export from DB SSOT.

**Scope — in:** Emit spans from attempt rows + pipeline steps; `gen_ai.*` mapping; OTLP config in `.env.example`.

**Scope — out:** Langfuse/LangSmith.

**Deliverables:** Staging trace in chosen backend.

**Depends on:** P3 (complete DB model).

---

## Next step

**`phase-execution`** from [waves/PIPELINE_OBSERVABILITY_P1_EXECUTION.md](./waves/PIPELINE_OBSERVABILITY_P1_EXECUTION.md) (P0 shipped [#92](https://github.com/raimondskrauklis/revy/pull/92)).
