# Finding resolution dogfood P3 — Staging sign-off (execution)

Phase **P3** of [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md). **P3 only.**

**Goal:** Operator sign-off at post-P2 deploy boundary; FR-DG1 + FR-DG2 tables complete; optional regrowth push.

## Decisions locked for P3

- **Sign-off `--since`:** post-P2 deploy job completion ISO (same as P2.4 boundary) — not PSA `11:38:12Z`.
- **Dogfood pushes:** push 1 (P0.4), push 2 FR-DG1 (P1.4), push 3 FR-DG2 (P2.4) — required; push 4 regrowth optional (P3.4).
- **SV-Q7:** [close chore PR without merge or memo-only merge](../staging-validation/STAGING_VALIDATION_FINDINGS.md#sv-q-registry-locked--open) after sign-off.
- **Probe cleanup:** remove `fr_dogfood/` from `main` in P3.3 if still present.

## Out of scope for P3

- New backend closure logic
- MR-DG1 → **P4**

---

## P3.1 — Deploy boundary + metrics run

**What:** Record post-P2 deploy ISO in memo; run metrics with `publish_summary` block; paste JSON snippet.

**Files:** `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:**

```bash
cd backend && DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics --since <POST_P2_DEPLOY_ISO> --json
```

---

## P3.2 — Pass criteria tables

**What:** Fill FR-DG1 (push 2) + FR-DG2 (push 3) tables: rev ids, `head_sha`, manifest fields, G9 excerpt, `pr_active_count`, inline count.

**Files:** `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:** Both gaps PASS or FAIL with evidence.

**Human gate:** Operator sign-off row signed.

---

## P3.3 — Doc sync

**What:** Update README + execution index (Done + sha); findings FR-DG1/FR-DG2 → **closed**; [staging-validation/README.md](../../staging-validation/README.md).

| Doc | Change |
|-----|--------|
| `finding-resolution-dogfood/README.md` | Execution table Done |
| `finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_FINDINGS.md` | FR-DG1/2 closed |
| `staging-validation/README.md` | Dogfood PR closed |
| `waves/FINDING_RESOLUTION_DOGFOOD_EXECUTION.md` | Phase statuses |

**Deliverable:** Rows consistent; probe fixture removed from `main`.

---

## P3.4 — Optional push 4 regrowth

**What:** Re-introduce probe issue on chore PR; single push; wait for agent; record block-1 regrowth (optional — FR-DG2 sign-off does not require this). Natural follow-up if push 3 removed code and operator wants regrowth probe.

**Files:** probe module (re-add), staging memo push-4 row

**Deliverable:** Memo row or explicit N/A.

**Human gate:** Wait for agent between pushes.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_fr_dogfood_probe.py tests/unit/test_github_resolution_metrics.py tests/unit/test_github_finding_closure.py tests/unit/test_github_publish_formatter.py tests/unit/test_judge_json_contract_staging_metrics.py -q
```

**Human gate:** P3.2 operator sign-off complete.

**Next:** none (wave A). Wave B: [FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md)
