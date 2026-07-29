# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C3_EXECUTION.md

# C3 — Staging sign-off Track C (execution)

Phase **C3** of [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md). Baseline: findings § Verification. **C3 only.**

**Goal:** FR-DG2 + FR-CS1/6/7 closed PASS on staging after C1+C2 deploy.

## Decisions locked for C3

- Deploy boundary `--since`: C1+C2 droplet job completion ISO (VAL9 pattern).
- Dogfood pushes: **backend only** (VAL8); one push per Revy cycle.
- Primary sign-off: per-group `state` + `resolution_method`, not `pr_active_count` alone.
- Probe: new chore PR `chore/fr-dg2-track-c-staging` — do not reuse #67 for product fix.

## Out of scope for C3

- Code changes unless repro fails → hotfix branch off `fix/fr-closure-scope-hygiene`
- MR-DG1

---

## C3.0 — Delete-only publish smoke

**What:** After deploy, confirm delete-only push still completes Moonshot + reconcile + publish (non-empty unified diff).

**Files:** none (operator)

**Deliverable:** Staging memo row C3.0 PASS or documented blocker.

---

## C3.1 — Introduce probe

**What:** New backend probe file with one intentional defect; push 1; ≥1 active group in DB.

**Files:** `backend/tests/fixtures/fr_dg2_track_c/` (or equivalent minimal probe)

**Deliverable:** Group id + revision id recorded in [staging memo](../../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) Track C.

---

## C3.2 — Age cohort (optional)

**What:** Unrelated backend commit; publish completes; cohort `last_seen` ages.

**Deliverable:** Memo row; revision SHA.

---

## C3.3 — Aged delete sign-off

**What:** Delete probe file. Target group(s) → `absent_and_addressed`; G9 shows path-removed line if hygiene; inline collapse.

**Deliverable:**

```bash
cd backend && python -m scripts.judge_json_contract_staging_metrics --since <C2_DEPLOY_ISO> --json
```

Per-group DB evidence: `state`, `resolution_method`, `last_seen_revision_id`, `resolved_at_revision_id`.

---

## C3.4 — Rename guard (non-gate if timeboxed)

**What:** Rename probe file; old-path groups remain **active** (R1).

**Deliverable:** Memo row PASS/FAIL.

---

**Phase gate** (automated — pre-push):

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_finding_closure.py -q
```

**Human gate:** C3.3 per-group DB + publish inspection signed in staging memo. LOOP stops until operator records PASS.

**Deploy:** requires C1+C2 on staging before C3.1.

**Next:** [`FINDING_RESOLUTION_CLOSURE_SCOPE_C4_EXECUTION.md`](./FINDING_RESOLUTION_CLOSURE_SCOPE_C4_EXECUTION.md)
