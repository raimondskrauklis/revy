# Finding resolution dogfood P2 — FR-DG2 stale retirement (execution)

Phase **P2** of [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md). Baseline: findings § FR-DG2. **P2 only.**

**Goal:** After P2 deploy, removing flagged probe code closes group, shrinks block 2 `pr_active_count`, resolves stale inline per GH-1v2.

## Decisions locked for P2

- **Pass 2 home:** `apply_pass2_closure_for_review_run` in `github_finding_closure.py` (invoked from `reconcile_tasks.py` ~line 52) — not fingerprint matching in `github_finding_reconcile.py`.
- **Absent + addressed:** fingerprint not in run N + Pass 1 `resolution_status=addressed` → `state=resolved`, `resolution_method=absent_and_addressed` (FR-Q3); uses P1 shared prior-revision helper.
- **Stale active groups:** FR-DG2 gap is groups **staying active** when fingerprint absent — `_load_pr_active_groups` already filters `state == active` (`github_publish.py` ~1005–1008); P2.1 closes them, P2.2 adds regression tests only if needed.
- **Thread collapse:** `_fingerprints_to_resolve_inline_threads` + `_resolve_stale_inline_threads` for closed groups and `line: null` orphans.
- **Dogfood push 3 (P2.4):** **after P2 merge + deploy** — delete or gut probe file; validates FR-DG2 only (push 2 already validated FR-DG1).

## Out of scope for P2

- Manifest / G9 denominator → **P1** (done)
- Moonshot → **P4**
- Optional regrowth → **P3.4**

---

## P2.1 — Pass 2 absent closure

**What:** Ensure `apply_pass2_closure_for_review_run` closes groups when fingerprint absent from current run and Pass 1 stamped `addressed`; unit tests with mock groups + prior-revision helper.

**Files:** `backend/app/services/github_finding_closure.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -q
```

---

## P2.2 — PR-wide count parity regression

**What:** Assert `pr_active_count` / block 2 rows exclude groups closed in P2.1; extend existing formatter/publish tests — no new query filter unless test proves gap.

**Files:** `backend/tests/unit/test_github_publish_formatter.py`, `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py tests/unit/test_github_publish.py -k "pr_active or verdict or absent" -q
```

---

## P2.3 — Stale inline thread resolve

**What:** Closed-group fingerprints and orphaned threads resolve on publish; mock GraphQL in unit tests.

**Files:** `backend/app/services/github_publish.py`, `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "resolve_stale or inline_thread" -q
```

---

## P2.4 — Merge, deploy, dogfood push 3 (FR-DG2)

**What:** Merge P2 to `main`; wait for droplet deploy; record **post-P2 deploy ISO**; chore PR **single commit** removing probe code; push; **wait for agent**.

**Pass criteria (push 3):** `pr_active_count` ↓ vs push 2; stale inline collapsed; group `resolved` + `absent_and_addressed` in DB.

**Files:** remove `backend/tests/fixtures/fr_dogfood/`, update `test_fr_dogfood_probe.py` or delete, staging memo push-3 row

**Deliverable:** Memo push-3 row PASS for FR-DG2.

**Human gate:** P2 deployed before push 3; operator verifies GitHub inline state.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_closure.py tests/unit/test_github_publish_formatter.py tests/unit/test_github_publish.py -q
```

**Next:** [FINDING_RESOLUTION_DOGFOOD_P3_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P3_EXECUTION.md)
