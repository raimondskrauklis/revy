# Pipeline observability P5 — OTel OTLP + doc sync (execution)

Phase **P5** of [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](../PIPELINE_OBSERVABILITY_GENERAL_PLAN.md). Baseline: findings §External research, PO-Q6. **P5 only — final phase.**

**Goal:** Optional OTLP export from DB SSOT (`gen_ai.*` mapping); program doc sync and README status closeout.

## Decisions locked for P5

- Span export reads `github_llm_call_attempts` + `github_pipeline_steps` — no third schema.
- Parent trace id = `pipeline_run_id`; attributes: `gen_ai.operation.name`, `gen_ai.usage.*`, `gen_ai.response.finish_reasons`, `failure_class`.
- **Export hook site (PO-Q19):** call `export_pipeline_run_spans(pipeline_run_id)` **idempotently** at each pipeline stage terminal commit — review (`review_tasks`), reconcile/judge (`reconcile_tasks`), publish (`github_publish.py` check finalize). **Not** review-only — full pipeline trace must include judge + publish spans.
- Config: `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME=revy-pipeline` in `backend/.env.example` — export disabled when unset.
- 100% sampling on staging when enabled; head sampling configurable via env.
- No Langfuse/LangSmith integration.

## Out of scope for P5

- Bedrock instrumentation (PO-Q13 follow-on)
- Vendor billing APIs (PO-Q12)
- Frontend dashboards

---

## P5.1 — OTLP span mapper

**What:** `backend/app/observability/otel_export.py` — `export_pipeline_run_spans(pipeline_run_id)` builds OTLP-compatible payloads from all attempt rows + steps for the run (idempotent full re-export).

**Files:** `backend/app/observability/otel_export.py`, `backend/tests/unit/test_otel_export.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_otel_export.py -q
```

---

## P5.2 — Stage-terminal export hooks + env config

**What:** After terminal commit at each stage, if OTLP endpoint set, call `export_pipeline_run_spans` (log failures, never raise). Hook sites: `review_tasks` (post-review), `reconcile_tasks` (post-judge), `github_publish.py` (post-publish check). Document in `.env.example`.

**Files:** `backend/app/core/config.py`, `backend/app/workers/review_tasks.py`, `backend/app/workers/reconcile_tasks.py`, `backend/app/services/github_publish.py`, `backend/.env.example`, `backend/tests/unit/test_otel_export_hook.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_otel_export_hook.py -q
```

---

## P5.3 — Doc sync (final)

**What:** Update program README execution table (all phases Done + sha); sync [docs/review-pipeline/README.md](../../README.md); findings §Shipped table.

| Doc | Change |
|-----|--------|
| [waves/PIPELINE_OBSERVABILITY_EXECUTION.md](./PIPELINE_OBSERVABILITY_EXECUTION.md) | All phases Done + commit sha |
| [README.md](../README.md) | Status → shipped |
| [PIPELINE_OBSERVABILITY_FINDINGS.md](../PIPELINE_OBSERVABILITY_FINDINGS.md) | Shipped table |
| [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](../PIPELINE_OBSERVABILITY_GENERAL_PLAN.md) | Program status note |

**Deliverable:** Grep confirms no `pending` in execution index.

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/observability/ app/workers/review_tasks.py app/workers/reconcile_tasks.py app/services/github_publish.py
pipenv run pytest tests/unit/test_otel_export.py tests/unit/test_otel_export_hook.py -q
```

**Human gate (non-blocking):** Operator validates full-pipeline spans (review + judge + publish) in OTLP backend on staging.

**Next:** none — program complete.
