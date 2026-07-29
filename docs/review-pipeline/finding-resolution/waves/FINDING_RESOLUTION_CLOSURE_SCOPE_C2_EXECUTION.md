# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C2_EXECUTION.md

# C2 — Manifest + G9 honesty (execution)

Phase **C2** of [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md). Baseline: findings § CS-Q6. **C2 only.**

**Goal:** Hygiene path-removed closures excluded from `resolution_rate_pct` and visible in G9 publish block.

## Decisions locked for C2

- Hygiene closure predicate: `resolved` + `absent_and_addressed` + `resolved_at_revision_id == current` + `last_seen_revision_id NOT IN prior_revision_ids`.
- Manifest field: `hygiene_path_removed_count` (int).
- G9 line: `- **Closed as path removed:** N (outside this push pair)` when N > 0.
- Do **not** ship C1 without C2 (rate lie risk).

## Out of scope for C2

- i18n LV for GitHub markdown (English publish only — existing pattern).
- Staging validation → **C3**

---

## C2.1 — Manifest exclusion predicate

**What:** Update `build_resolution_pass_manifest` to identify hygiene transitions, exclude from `transition_count` and `denominator_active_prior`, set `hygiene_path_removed_count`.

**Files:** `backend/app/services/github_resolution_metrics.py`, `backend/tests/unit/test_github_resolution_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py -q -k "manifest and hygiene"
```

---

## C2.2 — G9 formatter line

**What:** `format_resolution_metrics_block` renders path-removed line from manifest; fallback publish includes it when manifest present.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -q -k "resolution_metrics or path_removed"
```

---

## C2.3 — Pipeline trace parity

**What:** Ensure `resolution_pass` manifest written by reconcile includes new field; staging metrics script tolerates optional key (no crash if absent on old runs).

**Files:** `backend/app/services/github_pipeline_trace.py` (if needed), `backend/tests/unit/test_github_pipeline_trace.py`, `backend/scripts/judge_json_contract_staging_metrics.py` (read-only tolerance only if required)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py tests/unit/test_judge_json_contract_staging_metrics.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint
pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_publish_formatter.py tests/unit/test_github_pipeline_trace.py -q
```

**Deploy:** record droplet workflow completion ISO for C3 `--since`.

**Next:** [`FINDING_RESOLUTION_CLOSURE_SCOPE_C3_EXECUTION.md`](./FINDING_RESOLUTION_CLOSURE_SCOPE_C3_EXECUTION.md)
