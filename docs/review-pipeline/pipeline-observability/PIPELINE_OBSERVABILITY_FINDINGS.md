# Pipeline observability — findings

**Date:** 2026-08-10  
**Purpose:** Baseline for **production-grade observability** across the full Revy review pipeline — traces, tokens, cost, latency, and typed failures on every stage and every LLM call. **No execution steps.**

**Evidence:** Code on `main` (incl. PR #90); staging DB `revy-staging`; [OTel GenAI conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/); architecture peer review [pass-01](./reviews/architecture-peer-review/pass-01-2026-08-10.md) · [pass-02](./reviews/architecture-peer-review/pass-02-2026-08-10.md) (**BLOCK: no**).

---

## Summary

Revy has **partial** observability: judge tokens + manifest on Anthropic; `context_stats` on successful review runs; pipeline steps written **end-of-task** when `_run` completes (success or many in-run failures). The real gap is **abort paths** — Celery soft-kill, retryable `httpx.TimeoutException` (up to 3 retries), and permanent `_mark_failed` before retrieve/review — where `flush()` without `commit()` rolls back `context_stats` and leaves no attempt rows.

We lack a **unified LLM call record** (tokens, finish_reason, wait_ms, failure class) for Moonshot reviewer, Moonshot publish formatter, and Voyage embeddings; no **per-run cost rollup**; no **live pipeline step progress** during long LLM waits.

**Operator thesis (validated):** Industry standard is **one trace per review run** with child spans/steps per stage, **every LLM HTTP attempt** persisted with `gen_ai.usage.input_tokens` / `output_tokens` and `finish_reason`, and **typed failure taxonomy** — not raw exception strings. PR #89 `SoftTimeLimitExceeded` runs are a **symptom** of missing commit boundaries, not the program scope.

---

## Build principles

1. **One trace per review run** — parent = pipeline run / review run; children = index, retrieve, embed, review `chat`, judge `chat`, publish `chat`.
2. **Every LLM call gets a row** — tokens, model requested vs served, finish_reason, wait_ms, http_status, `failure_class`; align field names with OTel `gen_ai.*` for future OTLP export.
3. **Durable commit graph** — observability writes use **explicit `commit()`** (or dedicated short-lived sessions), not `flush()` alone on the worker's main session. See [Commit graph](#commit-graph-locked-p0) below.
4. **Content in artifacts, not indexes** — prompts/completions as pipeline artifacts or span events; DB columns hold previews (≤512 chars) + SHA-256 hash only.
5. **DB is SSOT for staging sign-off** — scripts + memos; OTel/Grafana optional export in later phase.
6. **No imputation** — missing tokens = `null`, not estimated; cost computed only when token counts exist.
7. **Estimated cost first, vendor actual later** — v1 `estimated_usd` = tokens × static price table; **real money** from provider billing APIs is **deferred** (PO-Q12).

---

## Commit graph (locked P0)

`LlmCallRecorder` owns all attempt-row writes. Each boundary is its **own transaction** (commit before returning to caller):

| # | When | Persists |
|---|------|----------|
| 1 | After retrieve, before review LLM | `context_stats`, `provider`, `model_id`, partial `timing_stats`, `failure_stage=retrieve` |
| 2 | Before each HTTP call | Attempt row `started` (or insert with `started_at`) |
| 3 | After HTTP returns (success or fail) | Attempt row tokens / `finish_reason` / `failure_class` / `wait_ms` |
| 4 | End of `run_review_run` (normal path) | Final `timing_stats`, pipeline steps, `token_rollup` partial |
| 5 | Worker final `commit` | Review run status + trace batch |
| 6 | `_mark_failed` (permanent, pre-retrieve) | `failure_stage`, `failure_class` on review run **in separate commit** when main txn never ran |

**Celery retries:** Steps 1–3 must survive worker retry — each uses `commit()`. Retryable `httpx.TimeoutException` leaves attempt row with `failure_class=timeout` and `attempt_no` incremented on next try.

**Prerequisite (shipped):** `revy_revision_llm_http_timeout_seconds` — 60s below Celery soft limit (PR #90 on `main`). Not a P0 deliverable.

---

## Terminology

| Term | OTel / Revy mapping |
|------|---------------------|
| **Workflow** | One `github_review_runs` row + `github_pipeline_runs` trace (`gen_ai.workflow.name` = `revy_pr_review`) |
| **Operation** | `index` · `retrieval` · `chat` · `embeddings` · `reconcile` · `publish` |
| **LLM attempt** | Single HTTP completion — one row in `github_llm_call_attempts` |
| **Stage timing** | Wall-clock ms per stage in `timing_stats` JSONB |
| **Failure class** | Shared taxonomy on review runs **and** attempt rows: `timeout` · `rate_limit` · `provider_error` · `truncated` · `parse_error` · `context_length` · `celery_soft_limit` · `superseded` |
| **Token rollup** | Sum of `input_tokens` / `output_tokens` across attempts on a run |
| **Estimated cost** | `token_rollup.estimated_usd` — from `llm_pricing` config; label **estimated** |
| **Vendor actual spend** | Provider billing API — **deferred** (PO-Q12) |

**Naming:** Use **`failure_class`** everywhere (DB, logs, metrics). Retire judge log values `parse` / `http` / `empty_body` — map to taxonomy in P0 (`parse` → `parse_error`, `http` → `provider_error`, `empty_body` → `parse_error`).

---

## Revy pipeline → OTel trace model

```text
invoke_workflow  revy_pr_review  (pipeline_run / review_run)
├── index          (index job — chunk, embed_batches; Voyage embeddings)
├── retrieval      (compare, supplemental search, RCX)
│   └── embeddings (per-query Voyage calls — optional child attempts)
├── chat           Moonshot reviewer
├── reconcile      (deterministic — no LLM)
├── chat           Anthropic judge × N candidates (staging: Anthropic/Claude — PO-Q13)
└── publish
    ├── chat       github_publish_formatter → moonshot_review._complete_chat
    └── (GitHub API — not gen_ai)
```

**Span naming:** `{operation} {model}` — e.g. `chat kimi-k2.7-code`, `embeddings voyage-3`.

---

## What exists vs genuinely new

### Shipped (verified)

| Asset | Location | Coverage |
|-------|----------|----------|
| Pipeline steps + artifacts | `github_pipeline_trace.py` | End-of-task terminal steps; judge tokens on step row |
| Judge token capture | `anthropic_review.py`, `github_finding_judge.py` | Per-candidate usage in manifest + step rollup |
| Judge structured logs | `judge_llm_request_started` / `completed` | duration_ms, model, candidate_id |
| Moonshot `finish_reason` | `moonshot_review.py` | `length` → truncated response error |
| `context_stats` JSONB | migration `0029` | Flushed pre-LLM; **committed only at task end** |
| HTTP timeout headroom | `config.py`, PR #90 | `revy_revision_llm_http_timeout_seconds` |
| Retryable HTTP timeout | `worker_retries.py` | `httpx.TimeoutException` → `WorkerRetryableError` |
| **`github_llm_call_attempts` + recorder** | `llm_call_recorder.py`, migration `0031` | P0 — per-attempt rows; dedicated session commits (PO-Q17) |
| **Review-run observability columns** | migration `0031`, `github_review_run.py` | `timing_stats`, `token_rollup`, `failure_stage`, `failure_class`, `trigger_source` |
| **Checkpoint commit after retrieve** | `review_run_observability.py`, `github_review.py` | Boundary #1 — survives HTTP timeout / Celery retry (PO-V3) |
| **`llm_pricing` skeleton** | `llm_pricing.py` | Static price map — `estimated_usd` computation in P3 |
| **`trigger_source` on review runs** | `create_review_run` | Copied from completed index job (PO-Q15) |
| **Attempt purge cascade** | `purge_old_pipeline_artifacts` | FK `pipeline_run_id` ON DELETE CASCADE (P0) |
| `PipelineStepStatus.processing` | `enums.py` | Exists; writers do not use it yet |
| Pipeline purge O8 | `purge_old_pipeline_artifacts` | Cascades runs → steps/artifacts; 90d retention |
| Staging scripts | `judge_json_contract_staging_metrics.py`, etc. | Operator SQL; legacy Moonshot CSV script not SSOT |

### Gaps (genuinely new)

| Gap | Severity | Industry pattern | P0 status |
|-----|----------|------------------|-----------|
| No **durable checkpoint** (flush ≠ commit) | **critical** | Mid-task commit before slow LLM | **P0 shipped** — boundary #1 |
| Attempt rows lost on **Celery retry** / soft-kill | **critical** | Per-attempt commit graph | **P0 shipped** — timeout path + `attempt_no` resume |
| No **Moonshot token persistence** on review/publish | **high** | `gen_ai.usage.*` on every `chat` span | P1 |
| No **`github_llm_call_attempts` table** | **high** | Per-call audit trail | **P0 shipped** |
| No **live step progress** (`processing` → terminal) | **high** | Abort visibility during long LLM wait | P2 |
| `_mark_failed` skips retrieve/review observability | **high** | `failure_stage` / `failure_class` on permanent fail | **P0 shipped** — boundary #6 |
| No **per-run token/cost rollup** | **high** | Σ(tokens × `llm_pricing`) | P3 |
| No **`llm_pricing` config** | **high** | Blocks `estimated_usd` (P3) | **P0 skeleton** — rates in P3 |
| Attempt rows **not in purge cascade** | **high** | FK from `pipeline_run_id`; extend O8 purge | **P0 shipped** |
| **Voyage** calls invisible | **medium** | `embeddings` attempts; null tokens + batch count (PO-Q11) |
| No **p95/p99** in metrics scripts | **medium** | SRE percentiles |
| **Bedrock** instrumentation | **low** | Deferred — separate `bedrock_review.py` path; not used in staging today (PO-Q13) |
| No **OTel OTLP export** | **low** | P5 |

### Reuse traps

| Trap | Detail |
|------|--------|
| End-of-task ≠ success-only | Many in-run failures get terminal pipeline steps when `_run` completes; abort/`_mark_failed` is the hole |
| `context_stats` NULL | Txn rollback or never reached retrieve — not proof of pre-LLM crash |
| `review_run_id` on index embed attempts | **Nullable** — index runs before review run exists; require `pipeline_run_id` when present |
| Manual-index embed jobs | No `pipeline_run_id` on manual index jobs — **skip embed attempt rows** (v1 out of scope) |
| Publish LLM | `github_publish_formatter` → `_complete_chat` — instrument at `_complete_chat` with caller `step_type` |
| `trigger_source` on review runs | Set in **`create_review_run`** from `get_latest_completed_index_job` (both pipeline + API enqueue paths) |
| Judge tokens ≠ run cost | Moonshot review dominates input tokens |

---

## External research — patterns to adopt

(Sources unchanged — OTel GenAI, Uptrace RAG, etc.)

| Pattern | Adopt | Notes |
|---------|-------|-------|
| `gen_ai.usage.*` on every LLM call | **yes** | Moonshot `usage`; Anthropic parsed; Voyage null until API returns usage |
| `failure_class` / `error.type` taxonomy | **yes** | Single enum — see Terminology |
| Mid-span checkpoint commits | **yes** | Commit graph above |
| Tail sampling | **defer** | Sentry manual today |
| Third-party LLM SaaS | **reject v1** | DB + scripts first |

---

## Metric catalog (target state)

### 1 — `github_llm_call_attempts` (PO-Q3)

One row per HTTP attempt (incl. Celery retries). Maps to OTel `chat` / `embeddings` spans.

| Column | Notes |
|--------|-------|
| `id` | UUID PK |
| `pipeline_run_id` | **Required** FK when row is written — cascade delete with O8 purge. **Omit attempt row** when no pipeline run (manual index). |
| `review_run_id` | **Nullable** — null for index-embed attempts |
| `index_job_id` | Nullable — link embed attempts to index job |
| `step_type` | `review` · `judge` · `publish` · `index_embed` |
| `operation_name` | `chat` · `embeddings` |
| `attempt_no` | 0-based; increments on Celery/parse retry |
| `provider` | `moonshot` · `anthropic` · `bedrock` · `voyage` |
| `request_model` / `response_model` | |
| `input_tokens` / `output_tokens` | Nullable |
| `finish_reason` | |
| `wait_ms` | HTTP wall time |
| `http_status` | |
| `failure_class` | Nullable on success — **same taxonomy as review run** |
| `response_preview` | ≤512 chars |
| `response_sha256` | |
| `batch_size` | Nullable — Voyage embed batch count when tokens null |
| `started_at` / `completed_at` | | `(pipeline_run_id)`, `(review_run_id, step_type)` where not null, `(started_at)`, `(provider, request_model)`.

### 2 — `github_review_runs` extensions

| Field | Purpose |
|-------|---------|
| `timing_stats` JSONB | `stats_version: 1`, per-stage ms |
| `token_rollup` JSONB | Totals + `estimated_usd` |
| `failure_stage` | Last stage before failure |
| `failure_class` | Shared taxonomy |
| `trigger_source` | Copied in **`create_review_run`** from linked completed index job (PO-Q15) |

### 3 — `llm_pricing` (PO-Q14)

Static config or small table: `(provider, model_id) → input_usd_per_1k, output_usd_per_1k`. **Owned in P0** (schema/config); consumed in P3 rollups. No prices in `model_catalog` today.

### 4 — `github_pipeline_steps`

| Rule | Detail |
|------|--------|
| P2: `processing` → terminal | New trace helpers — not just `_create_completed_step` |
| Token fields on LLM steps | Sum from attempt rows (P1) |

### 5 — Structured logs

| Event | Notes |
|-------|-------|
| `llm_call_started` / `completed` / `failed` | Unified names; **`failure_class`** field |
| `judge_llm_*` | **Dual-emit as aliases** through P3 (PO-Q9); remove in P4 |

### 6 — Staging metrics script (P4)

Primary reports: token totals, latency percentiles (`attempts.wait_ms`), failure taxonomy, truncation rate. Optional `--show-estimated-cost` (informational). Vendor API spend reconcile → PO-Q12 (not CSV).

---

## Catalog — instrumentation by stage

| Stage | LLM? | Target |
|-------|------|--------|
| **Index** | Voyage embed | Attempt rows **only when `pipeline_run_id` set**; null tokens + batch count |
| **Retrieve** | No | Incremental step + `timing_stats` |
| **Review** | Moonshot `chat` | Attempt rows + checkpoint commit before call |
| **Reconcile** | No | Incremental step |
| **Judge** | Anthropic `chat` | Attempt row per candidate — **P1 focus** (staging judge path) |
| **Publish** | Moonshot via formatter | `_complete_chat` with `step_type=publish` |

---

## Data scope & exclusions

| In scope | Out of scope (v1) |
|----------|-------------------|
| Moonshot, Anthropic (judge), Voyage on **pipeline-triggered** index | Exotic providers |
| Token-derived `estimated_usd` | Vendor billing APIs (PO-Q12) |
| O8 purge extension for attempts | Frontend dashboards |
| `bedrock` in provider enum / recorder contract | **Bedrock `bedrock_review.py` instrumentation** — deferred; not used in staging (PO-Q13) |
| Pipeline index embed attempts | Manual-index embed attempts (no `pipeline_run_id`) |

---

## Edge cases

| Case | Mitigation |
|------|------------|
| Celery retry after HTTP timeout | Attempt row committed with `failure_class=timeout`; `attempt_no`++ on retry |
| Celery soft-kill mid-LLM | Last attempt row + `failure_class=celery_soft_limit` if committed at start |
| `_mark_failed` before retrieve | Separate commit: `failure_stage`, `failure_class` |
| Parse retry (2× Moonshot) | Separate attempt rows `attempt_no` 0, 1 |
| Index embed before review run | `review_run_id=null`; write attempt only if `pipeline_run_id` from pipeline-trigger index |
| Superseded run | `failure_class=superseded` |

---

## Validation case — PR #89 (appendix)

Three `fbb2e26` runs: `SoftTimeLimitExceeded` ~900s; `context_stats` NULL; index-only pipeline trace. With commit graph: checkpoint + attempt row would survive.

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| PO-Q1 | DB SSOT vs OTel-first? | **locked** | DB first; OTLP maps from attempt rows (P5) |
| PO-Q2 | `timing_stats` + `token_rollup` JSONB? | **locked** | Yes — `stats_version: 1` |
| PO-Q3 | `github_llm_call_attempts`? | **locked** | Yes — one row per HTTP attempt |
| PO-Q4 | Full response on timeout? | **locked** | Preview ≤512 + sha256 |
| PO-Q5 | TTFT / streaming? | **locked** | Defer |
| PO-Q6 | OTel OTLP? | **locked** | P5; depends on P3 data model |
| PO-Q7 | HTTP timeout < Celery soft limit? | **locked** | **Shipped** PR #90 — prerequisite, not P0 |
| PO-Q8 | `failure_class` enum? | **locked** | Shared taxonomy on runs + attempts + logs |
| PO-Q9 | Unify `judge_llm_*` logs? | **locked** | Dual-emit aliases through P3; remove P4 |
| PO-Q10 | `estimated_usd` in DB? | **locked** | Yes — from `llm_pricing`; label estimated |
| PO-Q11 | Embed tokens? | **locked** | When Voyage returns usage; else null + batch count |
| PO-Q12 | Vendor billing APIs? | **locked** | Defer |
| PO-Q13 | Bedrock in P1? | **locked** | **Not dropped** — `bedrock` stays in provider enum + `LlmCallRecorder` contract. **P1 does not instrument** `bedrock_review.py` (separate boto Converse path); follow-on when Bedrock is enabled in an env. Staging judge = Anthropic/Claude only. |
| PO-Q14 | `llm_pricing` + attempts retention? | **locked** | **`llm_pricing` in P0**; attempts FK cascade + O8 purge extension in **P0** |
| PO-Q15 | `trigger_source` on review runs? | **locked** | Set in **`create_review_run`** from `get_latest_completed_index_job` |
| PO-Q16 | Manual-index embed attempts? | **locked** | **Omit** — no `pipeline_run_id`; out of v1 observability scope |
| PO-Q17 | Recorder session strategy? | **locked** | Dedicated `get_db_context()` for attempt rows (#2–#3); checkpoint #1 on shared session + `refresh(run)` |
| PO-Q18 | Review LLM latency SSOT? | **locked** | `github_llm_call_attempts.wait_ms` (`step_type=review`); mirror in `timing_stats.review_llm_wait_ms` |
| PO-Q19 | OTLP export hook site? | **locked** | Idempotent `export_pipeline_run_spans` at review + judge + publish terminal commits |

---

## Experiment / verification

| ID | Pass |
|----|------|
| PO-V1 | Successful run: Moonshot review + publish attempt rows with tokens |
| PO-V2 | `token_rollup` equals sum of attempt rows |
| PO-V3 | Induced **HTTP timeout** (retryable): attempt row `failure_class=timeout`, checkpoint `context_stats` present, survives Celery retry — **P0 only** (no success-path tokens; those are PO-V1/P1) |
| PO-V4 | Metrics script: p95 review LLM wait (`attempts.wait_ms`), failure taxonomy, truncation rate |
| PO-V5 | **Deferred** — vendor account APIs (Moonshot/Anthropic/Voyage) reconcile vs attempts (PO-Q12); no CSV |
| PO-V6 | `finish_reason=length` → `failure_class=truncated` |

---

## Devil's advocate

- **Storage growth** — attempts × judge candidates × retries; O8 purge cascade (PO-Q14).
- **Dual write** — `LlmCallRecorder` single writer for attempts + step token sums.
- **Price table staleness** — `estimated_usd` indicative until PO-Q12 vendor reconcile.
- **Mid-task commits** — accepted; observability durability outweighs single-txn purity on Celery workers.

---

## References

| Topic | Path |
|-------|------|
| Pipeline trace | `backend/app/services/github_pipeline_trace.py` |
| Review task commit | `backend/app/workers/review_tasks.py` |
| Review run | `backend/app/services/github_review.py` |
| Moonshot | `backend/app/integrations/moonshot_review.py` |
| Anthropic judge | `backend/app/integrations/anthropic_review.py` |
| Bedrock (deferred) | `backend/app/integrations/bedrock_review.py` |
| Publish formatter | `backend/app/services/github_publish_formatter.py` |
| Worker retries | `backend/app/workers/worker_retries.py` |
| OTel GenAI | https://opentelemetry.io/docs/specs/semconv/gen-ai/ |
