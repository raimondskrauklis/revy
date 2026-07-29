# Finding resolution dogfood P1 — FR-DG1 manifest & G9 (execution)

Phase **P1** of [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md). Baseline: findings § FR-DG1. **P1 only.**

**Goal:** Fix push that publishes yields `denominator_active_prior` ≥ 1, `transitions_addressed` ≥ 1, G9 prose not `n/a`.

## Decisions locked for P1

- **Prior revision selection:** `get_resolution_metrics_for_review_run` / manifest builder walks revisions backward to last with `publish_status=completed`, skipping `skipped_not_head`.
- **Pass 1 unchanged semantics:** still stamps on `synchronize` before pipeline; P1 only fixes pairing at publish time if that was the gap — if root cause is Pass 1, wire stamp cohort into manifest denominator explicitly.
- **G9:** `build_g9_resolution_prose` emits addressed line when `transitions_addressed` > 0; keep `n/a` only when denominator is legitimately 0 (first revision on PR).
- **No P2 closure changes** in this phase.

## Out of scope for P1

- Absent-fingerprint group `state=resolved` → **P2**
- Moonshot prompt → **P4**
- Full staging sign-off → **P3**

---

## P1.1 — Repro confirmation test

**What:** Unit test simulating rev N−1 `skipped_not_head` + rev N publish — documents expected denominator source (fails before fix, passes after).

**Files:** `backend/tests/unit/test_github_resolution_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py -k "skipped_not_head or prior_published" -q
```

---

## P1.2 — Last-published prior revision helper

**What:** Helper on pull request revisions returning prior revision id/sha with completed publish; use in `get_resolution_metrics_for_review_run`.

**Files:** `backend/app/services/github_resolution_metrics.py`, `backend/app/services/github_publish.py` (if publish job lookup lives there)

**Deliverable:** Helper covered by P1.1 tests.

---

## P1.3 — Manifest denominator + transitions

**What:** `build_resolution_pass_manifest` uses last-published prior for `denominator_active_prior` and transition pairing; `summary_json.resolution` populated on publish.

**Files:** `backend/app/services/github_resolution_metrics.py`, `backend/app/services/github_publish_formatter.py` (summary_json build path)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_publish_formatter.py -k "resolution" -q
```

---

## P1.4 — Dogfood push 2 (fix probe)

**What:** Single commit fixing P0 probe issue; push; **wait for agent**. Fill staging memo push-2 row: G9 not `n/a`, `resolution.addressed` ≥ 1.

**Files:** `backend/tests/fixtures/fr_dogfood/probe_module.py`, staging memo

**Deliverable:** Operator row in `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md`.

**Human gate:** Wait for publish before P2.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_publish_formatter.py -q
```

**Next:** [FINDING_RESOLUTION_DOGFOOD_P2_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P2_EXECUTION.md)
