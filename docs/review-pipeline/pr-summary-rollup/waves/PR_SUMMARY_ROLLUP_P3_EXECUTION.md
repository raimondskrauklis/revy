# docs/review-pipeline/pr-summary-rollup/waves/PR_SUMMARY_ROLLUP_P3_EXECUTION.md

# P3 — Staging sign-off + doc sync (execution)

Phase **P3** of [`PR_SUMMARY_ROLLUP_GENERAL_PLAN.md`](../PR_SUMMARY_ROLLUP_GENERAL_PLAN.md). Baseline: [`PR_SUMMARY_ROLLUP_FINDINGS.md`](../PR_SUMMARY_ROLLUP_FINDINGS.md) §experiment/verification. **P3 only** (P4 readability follows).

**Goal:** Dogfood PASS on multi-revision PR post-deploy; program docs marked shipped.

## Decisions locked for P3

- Staging target: kp-platform or revy repo PR with **≥2 revisions** after P2 deploy.
- Pass criteria from findings verification table: PR summary + push block on rev ≥2; `pr_resolution_rollup` on job + PR row matches comment; dogfood script green.
- Note SOS orphan-filter dependency if SOS P2 sign-off still open — document in memo, do not block PSR sign-off on SOS P2 alone.
- No pre-program PR backfill (PSR-Q6).
- `frontend/src/data/changelog.json` — **out of scope** (GitHub-facing markdown only; no Revy UI surface).

## Out of scope for P3

- Time-series rollup API / org analytics (parking lot)
- `compute_check_conclusion` PR-wide alignment (separate program)

---

## P3.1 — Staging validation memo stub + deploy boundaries

**What:** Create `PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md` from staging template — deploy `--since` rows, dogfood PR table, pass criteria copied from findings §experiment/verification, push-2/3 check rows.

**Files:** `docs/review-pipeline/pr-summary-rollup/PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md`

**Deliverable:**

```bash
test -f docs/review-pipeline/pr-summary-rollup/PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md
```

---

## P3.2 — Operator dogfood run (multi-revision PR)

**What:** After staging deploy, run `revy_review_dogfood_staging_validation.py` against dogfood PR rev ≥2; capture `head_sha`, comment excerpt, `pr_resolution_rollup` JSON; fill memo Results + Sign-off tables.

**Files:** `docs/review-pipeline/pr-summary-rollup/PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md`

**Deliverable:** memo Sign-off row `Staging PASS` with evidence links (PR URL, job id, script output).

**Human gate:** LOOP stops until operator marks staging PASS in memo — even if unit tests pass locally.

---

## P3.3 — Doc sync (program closeout)

**What:** Update program README + execution index status rows to Done + commit sha; cross-link staging memo; grep sibling docs for stale “ready for create-execution-plan” wording.

**Files:** `docs/review-pipeline/pr-summary-rollup/README.md`, `docs/review-pipeline/pr-summary-rollup/waves/PR_SUMMARY_ROLLUP_EXECUTION.md`, `docs/review-pipeline/pr-summary-rollup/PR_SUMMARY_ROLLUP_GENERAL_PLAN.md` (execution index line only)

**Deliverable:**

| Doc | Change |
|-----|--------|
| `README.md` | Status → shipped; link staging memo |
| `waves/PR_SUMMARY_ROLLUP_EXECUTION.md` | P0–P3 rows Done + sha |
| `PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md` | Sign-off PASS filled |
| `PR_SUMMARY_ROLLUP_GENERAL_PLAN.md` | Execution index points to shipped table |

```bash
grep -r "ready for.create-execution-plan" docs/review-pipeline/pr-summary-rollup/ || true
```

---

**Phase gate** (from `backend/`):

```bash
cd backend && pipenv run pytest tests/unit/test_github_pr_resolution_rollup.py tests/unit/test_github_publish_formatter.py -q
```

**Non-gate (staging):** dogfood script against staging DB after deploy.

**Human gate:** P3.2 staging PASS in `PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md`.

**Next:** [P4 readability](../PR_SUMMARY_ROLLUP_P4_READABILITY_FINDINGS.md) — scan + `<details>` explain layer.
