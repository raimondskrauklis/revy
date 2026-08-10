# Pipeline observability P4 — staging metrics (execution)

Phase **P4** of [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](../PIPELINE_OBSERVABILITY_GENERAL_PLAN.md). Baseline: findings §Metric catalog §6, PO-V4. **P4 only.**

**Goal:** Operator script for **tokens, latency percentiles, failure taxonomy, truncation** — primary staging sign-off. Cost is informational only; vendor API spend reconcile deferred (PO-Q12).

## Decisions locked for P4

- New script: `backend/scripts/pipeline_observability_staging_metrics.py`.
- **PO-V4 latency SSOT:** p50/p95/p99 from `github_llm_call_attempts.wait_ms` where `step_type=review`; fallback/mirror from `timing_stats.review_llm_wait_ms` when attempts missing.
- **Truncation rate:** primary from attempt `finish_reason=length` where `step_type=review`; fallback from `failure_class=truncated` on review runs.
- Token totals by provider/model/step_type; `failure_class` counts.
- Optional `--show-estimated-cost` flag (off by default) — uses P3 `llm_pricing`; not a gate.
- **PO-V5 deferred:** no CSV reconcile; future vendor APIs (Moonshot / Anthropic / Voyage account APIs) under PO-Q12.
- `--po-gate` gates on latency, taxonomy, truncation, token coverage — not cost.
- Remove `judge_llm_*` dual-emit (PO-Q9 sunset).
- Add row to [staging-validation/README.md](../../staging-validation/README.md).

## Out of scope for P4

- CI enforcement (`SKIP_CI_TESTS`)
- Vendor billing dashboards / CSV import (PO-Q12)
- OTLP export → **P5**

---

## P4.1 — Metrics script core reports

**What:** CLI `--since-hours` (default 24): token totals; p50/p95/p99 review LLM wait from attempts; `failure_class` counts; truncation rate.

**Files:** `backend/scripts/pipeline_observability_staging_metrics.py`, `backend/tests/unit/test_pipeline_observability_staging_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_pipeline_observability_staging_metrics.py -q
```

---

## P4.2 — Optional cost display + attempt coverage report

**What:** `--show-estimated-cost` prints estimated USD from attempts × `llm_pricing` (informational). Default report: attempt row coverage (% runs with review + judge + publish attempts).

**Files:** `backend/scripts/pipeline_observability_staging_metrics.py`, `backend/tests/unit/test_pipeline_observability_staging_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_pipeline_observability_staging_metrics.py -q -k coverage
```

---

## P4.3 — `--po-gate` + staging-validation index

**What:** Gate mode for staging memos (latency p95, taxonomy, truncation thresholds — document in script docstring). Add pipeline-observability row to staging-validation README.

**Files:** `backend/scripts/pipeline_observability_staging_metrics.py`, `docs/review-pipeline/staging-validation/README.md`, `docs/utils/BACKEND_SCRIPTS_RUNBOOK.md`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_pipeline_observability_staging_metrics.py -q -k gate
```

---

## P4.4 — Sunset `judge_llm_*` log aliases

**What:** Remove dual-emit from `anthropic_review`; update tests.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review_observability.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review_observability.py tests/unit/test_anthropic_review.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check scripts/pipeline_observability_staging_metrics.py
pipenv run pytest tests/unit/test_pipeline_observability_staging_metrics.py tests/unit/test_anthropic_review_observability.py -q
```

**Human gate (non-blocking):** Operator runs script against `revy-staging` and records output in staging-validation memo.

**Next:** [PIPELINE_OBSERVABILITY_P5_EXECUTION.md](./PIPELINE_OBSERVABILITY_P5_EXECUTION.md)
