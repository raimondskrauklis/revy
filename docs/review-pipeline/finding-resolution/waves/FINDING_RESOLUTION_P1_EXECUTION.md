# Finding resolution P1 — Pass 1 + Pass 2 closure (execution)

Phase **P1** of [FINDING_RESOLUTION_GENERAL_PLAN.md](../FINDING_RESOLUTION_GENERAL_PLAN.md). Baseline: findings § multi-pass model. **P1 only.** Requires migration **0028** applied.

**Goal:** On new push, stamp `resolution_status` with compare-failure signal; after Moonshot reconcile, close groups when addressed + absent from run (FR-Q3); re-open on re-report (FR-Q13).

## Decisions locked for P1

- Pass 1: `apply_resolution_status_for_synchronize` sets `closure_blocked_reason=compare_failed` when compare API fails — **not** when file simply absent from delta; **clear** `closure_blocked_reason` when compare succeeds (avoids stale block from prior push).
- Pass 1: still **no** `group.state` flip on sync alone.
- Pass 2: runs inside `reconcile_tasks` immediately after `reconcile_review_run`, **before** `record_review_run_judge_status`.
- Absent + `resolution_status=addressed` → `state=resolved`, `resolution_method=absent_and_addressed`, `resolved_at_revision_id=current revision`.
- Re-reported fingerprint with `resolution_status=addressed` → keep `active`, clear false closure (FR-Q13).
- Discovery judge dismiss → set `resolution_method=judge_dismissed` on group (state already `resolved`).
- Do **not** close on heuristic alone without absent check (FR-Q2 guard).
- **Module split (locked):** `github_finding_closure.py` — Pass 2 orchestration (`apply_pass2_closure_for_review_run`); `github_finding_reconcile.py` — FR-Q13 re-open inside `reconcile_review_run` (replaces `elif group.state == resolved: pass` at line 157–158). **No** `github_finding_resolution.py`.
- **Worker order within reconcile (locked):** `reconcile_review_run` (re-open path) → Pass 2 closure → discovery judge → (Pass 3 + transitions added in P2/P3).
- **`reconcile_tasks` refactor (locked):** Remove early `record_reconcile_pipeline_step` call (today after discovery judge, ~line 55). Pass 2 runs **before** `record_review_run_judge_status`. Defer reconcile-step trace to **P3.1** (after transitions); P1 only wires Pass 2 + reorder.
- Same-revision re-report + `addressed` without absent fingerprint: stays `active`; `resolution_status` may remain `addressed` until next `synchronize` — test explicitly in P1.5.

## Out of scope for P1

- Pass 3 verification judge → **P2**
- Metrics manifest FR-Q12 → **P3**
- Human dismiss API → **P4**

---

## P1.1 — Compare-failed signaling (Pass 1)

**What:** Refactor `_fetch_compare_patches` to return `(patches_by_file, compare_failed: bool)`; stamp `closure_blocked_reason` on groups when compare fails; keep `resolution_status=still_open`.

**Files:** `backend/app/services/github_resolution_metrics.py`, `backend/tests/unit/test_github_resolution_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py -k "compare_failed or synchronize" -q
```

---

## P1.2 — Pass 2 closure + worker reorder

**What:** `apply_pass2_closure_for_review_run(session, review_run_id)` in `github_finding_closure.py` — uses fingerprints in run vs prior groups with `last_seen_revision_id == prior_revision`; calls closure rules from P0. Rewrite `reconcile_tasks.py` worker body to: `reconcile_review_run` → **Pass 2** → `record_review_run_judge_status` (discovery). Remove misplaced early `record_reconcile_pipeline_step` — reconcile trace deferred to P3.1.

**Files:** `backend/app/services/github_finding_closure.py`, `backend/app/workers/reconcile_tasks.py`, `backend/tests/unit/test_reconcile_tasks.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py tests/unit/test_reconcile_tasks.py -k closure -q
```

---

## P1.3 — FR-Q13 re-open on re-report

**What:** Inside `reconcile_review_run` (before Pass 2): when linking finding to group with `resolution_method=absent_and_addressed` and same fingerprint in current run → set `active`, clear `resolution_method`, update `last_seen_revision_id`. Replaces silent `elif group.state == resolved: pass`.

**Files:** `backend/app/services/github_finding_reconcile.py`, `backend/tests/unit/test_github_finding_reconcile.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_reconcile.py -k "reopen or resolved" -q
```

---

## P1.4 — Discovery judge sets `resolution_method`

**What:** On `GitHubJudgeOutcome.dismissed`, set `group.resolution_method=judge_dismissed` and `resolved_at_revision_id` from review run revision.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k dismiss -q
```

---

## P1.5 — Integration tests (push-to-close)

**What:** Test matrix: fix + absent → resolved; fix + re-report → active; same-revision re-report + addressed (no absent) → active, `resolution_status` may stay `addressed`; compare fail → still_open + blocked reason; judge dismiss → resolved + method.

**Files:** `backend/tests/unit/test_github_finding_closure.py`, `backend/tests/unit/test_github_resolution_metrics.py`, `backend/tests/unit/test_reconcile_tasks.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py tests/unit/test_github_resolution_metrics.py tests/unit/test_reconcile_tasks.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_closure.py tests/unit/test_github_finding_reconcile.py tests/unit/test_github_finding_judge.py tests/unit/test_github_resolution_metrics.py tests/unit/test_reconcile_tasks.py -q
pipenv run ruff check app/services/github_resolution_metrics.py app/services/github_finding_closure.py app/workers/reconcile_tasks.py app/services/github_finding_judge.py
```

**Human gate (non-gate):** staging PR — fix one ERROR inline, push again, confirm group `resolved` + thread resolve after publish.

**Next:** [FINDING_RESOLUTION_P2_EXECUTION.md](./FINDING_RESOLUTION_P2_EXECUTION.md)
