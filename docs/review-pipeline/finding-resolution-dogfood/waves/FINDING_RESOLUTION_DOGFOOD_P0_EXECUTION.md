# Finding resolution dogfood P0 — Repro & observability (execution)

Phase **P0** of [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md). Baseline: [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](../FINDING_RESOLUTION_DOGFOOD_FINDINGS.md). **P0 only.**

**Goal:** Staging probe, operator memo stub, resolution metrics in script, program SSOT — no closure logic changes yet.

## Decisions locked for P0

- Probe lives under `backend/tests/fixtures/fr_dogfood/` with one intentional fixable issue (unused const or obvious bug).
- Unit test loads probe via normal import path (no `importlib` hardcoded path).
- `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md` stub with deploy row + dogfood PR table empty.
- Metrics script adds `publish_summary` block: `generation_active_count`, `pr_active_count`, `resolution` aggregates from completed publish jobs in `--since` window.
- `active_program`: `finding-resolution-dogfood` in `.revy/review-context.json`.

## PR review context (first commit)

- **SSOT:** `.revy/review-context.json` — `active_program` + `programs[]` with execution, findings, general plan paths under `finding-resolution-dogfood/`
- **Greptile:** `cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --write`
- **Bugbot:** `.cursor/BUGBOT.md` — active program + three doc links

## Out of scope for P0

- `apply_resolution_status_for_synchronize` changes → **P1**
- Reconcile closure / thread resolve → **P2**
- Moonshot prompt → **P4**
- Staging sign-off tables → **P3**

---

## P0.0 — Program PR review context

**What:** Add `finding-resolution-dogfood` to SSOT, regenerate Greptile, update Bugbot active program.

**Files:** `.revy/review-context.json`, `.greptile/files.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --check
cd backend && pipenv run pytest tests/unit/test_generate_greptile_files.py -q
```

---

## P0.1 — Staging validation memo stub

**What:** Create `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md` with deploy table, `--since` placeholder, dogfood steps 1–3 outline, pass-criteria headers for FR-DG1/FR-DG2.

**Files:** `docs/review-pipeline/finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:** File exists; links from [README.md](../README.md).

---

## P0.2 — FR dogfood probe fixture

**What:** `probe_module.py` with one fixable maintainability target; `test_fr_dogfood_probe.py` asserts stable behavior.

**Files:** `backend/tests/fixtures/fr_dogfood/probe_module.py`, `backend/tests/unit/test_fr_dogfood_probe.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_fr_dogfood_probe.py -q
```

---

## P0.3 — Metrics script resolution probe

**What:** Extend `judge_json_contract_staging_metrics.py` JSON output with `publish_summary` section (completed publishes in window: count, p50 `generation_active_count`, `pr_active_count`, sum `resolution.addressed`). Unit test with mocked rows or fixture SQL strings.

**Files:** `backend/scripts/judge_json_contract_staging_metrics.py`, `backend/tests/unit/test_judge_json_contract_staging_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_judge_json_contract_staging_metrics.py -q
```

---

## P0.4 — Open dogfood PR (push 1)

**What:** Branch `chore/finding-resolution-staging-dogfood`; single commit with P0.0–P0.3; push; **wait for Revy** before any P1 work. Record deploy boundary when feature work merges (this PR opens post-boundary).

**Files:** (operator) open PR; fill memo push-0 row with `head_sha` + run id after agent completes.

**Deliverable:** PR open; rev 1 publish `completed` or operator notes INCONCLUSIVE.

**Human gate:** LOOP stops until agent finishes rev 1.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_fr_dogfood_probe.py tests/unit/test_judge_json_contract_staging_metrics.py tests/unit/test_generate_greptile_files.py -q
pipenv run python -m scripts.generate_greptile_files_from_review_context --check
```

**Next:** [FINDING_RESOLUTION_DOGFOOD_P1_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P1_EXECUTION.md)
