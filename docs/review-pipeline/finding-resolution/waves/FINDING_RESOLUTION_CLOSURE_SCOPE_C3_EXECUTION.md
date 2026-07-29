# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C3_EXECUTION.md

# C3 — Staging sign-off Track C (execution)

Phase **C3** of [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md). Baseline: findings § Verification + [dogfood post-validation](../../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md). **C3 only.**

**Goal:** FR-DG2 + FR-CS1/6/7 closed PASS on staging after C1+C2 deploy.

## Decisions locked for C3

- Deploy boundary `--since`: C1+C2 droplet job completion ISO (VAL9 pattern).
- Dogfood pushes: **backend only** (VAL8); one push per Revy cycle.
- Primary sign-off: per-group `state` + `resolution_method`, not `pr_active_count` alone.
- Probe PR: `chore/fr-dg2-track-c-staging` — do not reuse #67 for product fix.
- **Probe protocol (DG-PV lesson):** review-visible defect in importable module + `tests/unit/test_*_probe.py` importing fixture path (see `test_fr_dogfood_probe.py` / #67 `fr_dg2_probe` pattern) — not fixture-only unused const.

## Out of scope for C3

- Code changes unless repro fails → hotfix branch off `fix/fr-closure-scope-hygiene`
- MR-DG1
- R2 superseded-publish automated test — operator watches fast follow-up push on C3.3

---

## C3.0 — Delete-only publish smoke

**What:** After deploy, confirm delete-only push still completes Moonshot + reconcile + publish (non-empty unified diff).

**Files:** none (operator)

**Deliverable:** Staging memo row C3.0 PASS or documented blocker.

---

## C3.1 — Introduce review-visible probe

**What:** New package under `backend/tests/fixtures/fr_dg2_track_c/`: module with **PSA-class review-visible defect** (e.g. unsafe pattern Moonshot flags); `tests/unit/test_fr_dg2_track_c_probe.py` imports module so push is non-trivial. Push 1 → ≥1 active group with expected `file_path`.

**Files:** `backend/tests/fixtures/fr_dg2_track_c/`, `backend/tests/unit/test_fr_dg2_track_c_probe.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_fr_dg2_track_c_probe.py -q
```

Record group id + revision id in [staging memo](../../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) Track C.

---

## C3.2 — Age cohort (recommended for VAL10 shape)

**What:** Unrelated **backend** commit (not program docs); publish completes; primary probe group `last_seen` ages to rev 1.

**Deliverable:** Memo row with revision SHA + `last_seen_revision_id` before delete push.

---

## C3.3 — Aged delete sign-off

**What:** Delete probe file. Aged group(s) → `absent_and_addressed`; G9 shows `Closed as path removed` line; inline collapse. Optional: note if fast follow-up push occurs (R2 watch).

**Deliverable:**

```bash
cd backend && pipenv run python -m scripts.judge_json_contract_staging_metrics --since <C2_DEPLOY_ISO> --json
```

Per-group DB evidence: `state`, `resolution_method`, `last_seen_revision_id`, `resolved_at_revision_id`.

---

## C3.4 — Rename guard (non-gate if timeboxed)

**What:** On separate probe or second PR: rename file; old-path groups remain **active** (R1).

**Deliverable:** Memo row PASS/FAIL.

---

## C3.5 — FR-Q13 re-open (optional non-gate)

**What:** Re-add deleted file with same defect fingerprint; group re-opens per FR-Q13.

**Deliverable:** Memo row if run.

---

**Phase gate** (automated — before staging pushes):

```bash
cd backend && pipenv run lint
cd backend && pipenv run pytest \
  tests/unit/test_github_api.py \
  tests/unit/test_github_compare_patches.py \
  tests/unit/test_github_path_hygiene.py \
  tests/unit/test_github_resolution_metrics.py \
  tests/unit/test_github_finding_closure.py \
  tests/unit/test_github_publish_formatter.py \
  -q
```

**Human gate:** C3.3 per-group DB + publish inspection signed in staging memo. LOOP stops until operator records PASS.

**Deploy:** requires C1+C2 on staging before C3.1.

**Next:** [`FINDING_RESOLUTION_CLOSURE_SCOPE_C4_EXECUTION.md`](./FINDING_RESOLUTION_CLOSURE_SCOPE_C4_EXECUTION.md)
