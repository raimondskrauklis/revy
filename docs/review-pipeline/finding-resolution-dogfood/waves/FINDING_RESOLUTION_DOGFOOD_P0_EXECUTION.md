# Finding resolution dogfood P0 — Repro & observability (execution)

Phase **P0** of [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md). Baseline: [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](../FINDING_RESOLUTION_DOGFOOD_FINDINGS.md). **P0 only.**

**Goal:** Staging probe, operator memo stub, resolution metrics in script, program SSOT — no closure logic changes yet.

## Decisions locked for P0

- Probe lives under `backend/tests/fixtures/fr_dogfood/` with one intentional fixable issue (unused const — **wire on push 2**, remove file on push 3 after P2).
- Unit test loads probe via normal import path (no `importlib` hardcoded path).
- Staging memo stub includes **deploy-boundary table** (PSA baseline + placeholders for post-P1 / post-P2).
- Metrics script adds `publish_summary` block from completed publish jobs in `--since` window.
- `active_program`: `finding-resolution-dogfood` in `.revy/review-context.json`.
- **P0 metrics `--since`:** PSA post-#62 boundary `2026-07-29T11:38:12Z` only — not the P3 sign-off boundary.

## PR review context (first commit)

- **SSOT:** `.revy/review-context.json` — `active_program` + **`programs[]` with exactly one entry** (active program only; remove shipped programs)
- **Greptile:** `cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --write`
- **Bugbot:** `.cursor/BUGBOT.md` — active program + three doc links

## Out of scope for P0

- `apply_resolution_status_for_synchronize` changes → **P1**
- Reconcile closure / thread resolve → **P2**
- Moonshot prompt → **P4**
- FR-DG1/FR-DG2 staging sign-off → **P3**

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

**What:** Create `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md` with deploy-boundary table (PSA `11:38:12Z`, post-P1 TBD, post-P2 TBD), dogfood push outline (push 1 introduce / push 2 FR-DG1 / push 3 FR-DG2), pass-criteria headers.

**Files:** `docs/review-pipeline/finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:** File exists; links from [README.md](../README.md).

---

## P0.2 — FR dogfood probe fixture

**What:** `probe_module.py` with unused const; `test_fr_dogfood_probe.py` imports via package path.

**Files:** `backend/tests/fixtures/fr_dogfood/probe_module.py`, `backend/tests/unit/test_fr_dogfood_probe.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_fr_dogfood_probe.py -q
```

---

## P0.3 — Metrics script resolution probe

**What:** Extend `judge_json_contract_staging_metrics.py` JSON with `publish_summary` (counts, p50 `generation_active_count` / `pr_active_count`, sum `resolution.addressed`, manifest fields when present in trace).

**Files:** `backend/scripts/judge_json_contract_staging_metrics.py`, `backend/tests/unit/test_judge_json_contract_staging_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_judge_json_contract_staging_metrics.py -q
```

---

## P0.4 — Open dogfood PR (push 1)

**What:** Branch `chore/finding-resolution-staging-dogfood`; commit P0.0–P0.3; push; **wait for Revy**. Fill memo push-1 row (`head_sha`, run id). P0 does **not** record a new deploy boundary — use PSA baseline for optional P0.3 smoke run only.

**Files:** (operator) open chore PR; staging memo push-1 row.

**Deliverable:** PR open; rev 1 publish `completed`.

**Human gate:** LOOP stops until agent finishes push 1.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_fr_dogfood_probe.py tests/unit/test_judge_json_contract_staging_metrics.py tests/unit/test_generate_greptile_files.py -q
pipenv run python -m scripts.generate_greptile_files_from_review_context --check
```

**Next:** [FINDING_RESOLUTION_DOGFOOD_P1_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P1_EXECUTION.md)
