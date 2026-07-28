# Finding resolution P3 — Metrics & display (execution)

Phase **P3** of [FINDING_RESOLUTION_GENERAL_PLAN.md](../FINDING_RESOLUTION_GENERAL_PLAN.md). **P3 only.** Requires P1 closure methods populated in tests.

**Goal:** FR-Q12 transitions-only resolution rate on reconcile manifest; honest breakdown by `resolution_method`; G9 + GitHub metrics block; API exposes resolution fields.

## Decisions locked for P3

- `resolution_metrics` on **reconcile** step `resolution_pass` sub-artifact: `transitions_addressed`, `transitions_dismissed` (by method), `denominator_active_prior`, `resolution_rate_pct`, `compare_failed_count`.
- **Denominator (locked):** groups that were **`active` on N−1 at sync** (Pass 1 stamp cohort: `last_seen_revision_id == prior_revision`), **excluding** groups already `resolved` before sync and groups with `closure_blocked_reason=compare_failed`. Not the full non-superseded PR set.
- **Do not** scan live rows at publish for rate — use manifest from reconcile pass.
- **Worker timing (locked):** `compute_resolution_transitions` runs in `reconcile_tasks` **after Pass 3 verification** (P2), **before** `enqueue_publish_for_review_run` — so `verification_dismissed` transitions count toward FR-Q12.
- **Reconcile trace write (locked):** Add `_get_reconcile_pipeline_step` + `record_resolution_pass_on_reconcile_step` using `_upsert_step_manifest` (pattern: `github_pipeline_trace.py` publish/index upserts). Call **`record_reconcile_pipeline_step`** once at end of worker (linked_group_count + `resolution_pass` in same manifest). Do not create reconcile step mid-worker.
- `count_resolution_status` uses `resolution_method` — fix bug where any `state==resolved` counted as `judge_dismissed`.
- G9 prose + metrics block: addressed / dismissed breakdown / still open / rate %.
- `ReconciledFindingResponse`: add `resolution_status`, `resolution_method`, `resolved_at_revision_id`, `closure_blocked_reason` (nullable).
- Reviewer UI resolution labels + badges → **P4.5** (with dismiss action and FR-Q7).

## Out of scope for P3

- Human dismiss API → **P4**
- Reviewer UI / i18n → **P4.5**
- Workspace analytics dashboard
- Langfuse dashboards

---

## P3.1 — Compute transitions after Pass 3

**What:** `compute_resolution_transitions(session, pull_request, prior_revision, current_revision)` → manifest dict (transitions this pair only; denominator per locked rule above). Add `record_resolution_pass_on_reconcile_step` + `_get_reconcile_pipeline_step` in `github_pipeline_trace.py`; wire in `reconcile_tasks` **after** Pass 3, **before** `record_judge_pipeline_step` and publish enqueue. Move `record_reconcile_pipeline_step` here from mid-worker (P1 removed early call).

**Files:** `backend/app/services/github_resolution_metrics.py`, `backend/app/services/github_pipeline_trace.py`, `backend/app/workers/reconcile_tasks.py`, `backend/tests/unit/test_github_resolution_metrics.py`, `backend/tests/unit/test_github_pipeline_trace.py`, `backend/tests/unit/test_reconcile_tasks.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_reconcile_tasks.py -k "transitions or resolution_pass" -q
```

---

## P3.2 — Fix `count_resolution_status`

**What:** Map `judge_dismissed`, `verification_dismissed`, `human_dismissed`, `absent_and_addressed` from `resolution_method`; `still_open` from `resolution_status` on active groups.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k resolution -q
```

---

## P3.3 — G9 + metrics block in publish

**What:** `get_resolution_metrics_for_review_run(session, review_run_id)` reads reconcile-step `resolution_pass` from pipeline trace; `format_resolution_metrics_block(manifest)` appended to issue comment in `_build_publish_surface`. G9 still lists publishable inline findings for **this generation** only (FR-Q7 PR-level block deferred to P4.2).

**Files:** `backend/app/services/github_pipeline_trace.py`, `backend/app/services/github_publish_formatter.py`, `backend/app/services/github_publish.py`, `backend/tests/unit/test_github_publish_formatter.py`, `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py tests/unit/test_github_publish.py -k "resolution or metrics" -q
```

---

## P3.4 — API schema fields

**What:** Extend `ReconciledFindingResponse` + list endpoint serialization from `github_finding_groups`.

**Files:** `backend/app/schemas/github_review.py`, `backend/app/services/github_finding_reconcile.py`, `backend/app/api/v1/workspaces/installation_review.py`, `backend/tests/unit/test_github_reconciled_findings_routes.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_reconciled_findings_routes.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_publish_formatter.py tests/unit/test_github_publish.py tests/unit/test_github_reconciled_findings_routes.py tests/unit/test_reconcile_tasks.py tests/unit/test_github_pipeline_trace.py -q
pipenv run ruff check app/services/github_publish_formatter.py app/services/github_resolution_metrics.py app/services/github_pipeline_trace.py app/workers/reconcile_tasks.py
```

**Next:** [FINDING_RESOLUTION_P4_EXECUTION.md](./FINDING_RESOLUTION_P4_EXECUTION.md)
