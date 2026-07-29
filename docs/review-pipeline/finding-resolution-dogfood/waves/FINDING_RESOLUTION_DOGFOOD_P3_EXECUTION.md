# Finding resolution dogfood P3 — Staging sign-off (execution)

Phase **P3** of [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md). **P3 only.**

**Goal:** Operator sign-off on post-deploy worker; FR-DG1 + FR-DG2 pass tables filled; program index updated.

## Decisions locked for P3

- **3-push dogfood:** push 1 introduce (P0.4), push 2 fix (P1.4), push 3 optional re-introduce for regrowth probe.
- **Deploy boundary:** `--since` = droplet deploy job completion after P1+P2 merge to `main`.
- **SV-Q7:** close chore PR after sign-off or merge memo-only per operator choice.
- **Probe cleanup:** remove `backend/tests/fixtures/fr_dogfood/` from `main` in doc-sync subphase if dogfood merged probe files.

## Out of scope for P3

- New backend closure logic
- MR-DG1 (parallel **P4**)

---

## P3.1 — Deploy boundary + metrics run

**What:** Record deploy ISO after merge; run metrics script with `--since` + new `publish_summary` block; paste JSON snippet into staging memo.

**Files:** `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:**

```bash
cd backend && DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics --since <DEPLOY_ISO> --json
```

---

## P3.2 — Pass criteria tables

**What:** Fill FR-DG1 + FR-DG2 pass/fail tables with rev ids, `head_sha`, `summary_json`, issue-comment G9 excerpt, inline thread count.

**Files:** `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:** Both gaps marked PASS or FAIL with evidence links.

**Human gate:** Operator sign-off row signed.

---

## P3.3 — Doc sync

**What:** Update program README execution table (Done + sha); [staging-validation/README.md](../../staging-validation/README.md) active/next PR rows; findings gap registry FR-DG1/FR-DG2 → **closed** or **deferred** with reason.

| Doc | Change |
|-----|--------|
| `finding-resolution-dogfood/README.md` | Execution table status Done |
| `finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_FINDINGS.md` | FR-DG1/2 status |
| `staging-validation/README.md` | Dogfood PR closed / next track |
| `waves/FINDING_RESOLUTION_DOGFOOD_EXECUTION.md` | Phase statuses |

**Deliverable:** All rows consistent; remove ephemeral probe fixture if still on branch.

---

## P3.4 — Optional push 3 regrowth

**What:** Re-introduce probe issue; single push; wait for agent; record block-1 regrowth in memo (optional — not required for sign-off if FR-DG1/2 PASS).

**Files:** probe module, staging memo push-3 row

**Deliverable:** Memo row or explicit N/A.

**Human gate:** Wait for agent between pushes.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_fr_dogfood_probe.py tests/unit/test_github_resolution_metrics.py tests/unit/test_github_finding_closure.py -q
```

**Human gate:** P3.2 operator sign-off complete.

**Next:** none (wave A complete). Wave B: [FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md) optional parallel.
