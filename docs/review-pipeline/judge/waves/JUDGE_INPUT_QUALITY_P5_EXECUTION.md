# Judge input quality P5 — Staging validation gate (execution)

Phase **P5** of [JUDGE_INPUT_QUALITY_GENERAL_PLAN.md](../JUDGE_INPUT_QUALITY_GENERAL_PLAN.md). Baseline: [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](../JUDGE_INPUT_INVESTIGATION_FINDINGS.md) § Staging DB statistics. **P5 only — final phase.**

**Goal:** Staging proof that judge input quality improved vs investigation baseline; gateway + direct Anthropic paths verified.

## Decisions locked for P5

- Do **not** re-implement gateway client, config, or smoke script — use `backend/scripts/test_anthropic_judge_gateway.py` on gateway branch / merged `main`.
- Validation memo = appendix in findings or short section in [REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](../../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) Track link.
- Compare metrics: evidence %, `user_prompt` char avg, `file_patch_chars` when present, judge outcomes (small N).
- No R5-Q3 threshold changes; no Reviewer UI.

## Out of scope for P5

- Production deploy sign-off beyond staging
- `changelog.json` — no user-facing product change

---

## P5.1 — Smoke script (gateway + direct)

**What:** Run smoke script with gateway env vars; run with direct-only env; both succeed or document skip reason.

**Files:** `backend/scripts/test_anthropic_judge_gateway.py`

**Deliverable (non-gate if no credentials):**

```bash
cd backend && pipenv run python scripts/test_anthropic_judge_gateway.py
```

---

## P5.2 — Staging SQL replay

**What:** Execute P2 validation queries + judge prompt size query on `revy-staging` after P0–P4 deploy; record before/after table in validation memo.

**Files:** manual — `PRODUCTION_DATABASE_URL` per [DATABASE_CONNECTION_GUIDE.md](../../../utils/DATABASE_CONNECTION_GUIDE.md)

**Deliverable:** Metrics table in validation memo (non-gate — requires staging access).

---

## P5.3 — Validation memo

**What:** Add `JUDGE_INPUT_QUALITY_STAGING_VALIDATION.md` in `judge/` OR appendix § in findings — before/after metrics, smoke result, gateway model id if RTU Opus used.

**Files:** `docs/review-pipeline/judge/JUDGE_INPUT_QUALITY_STAGING_VALIDATION.md`

**Deliverable:** Memo file exists with dated results.

---

## P5.4 — Doc sync

**What:** Update program docs with shipped status and gap closures.

| Doc | Change |
|-----|--------|
| [judge/waves/JUDGE_INPUT_QUALITY_EXECUTION.md](./JUDGE_INPUT_QUALITY_EXECUTION.md) | Status Done + commit sha per phase row |
| [judge/README.md](../README.md) | Link validation memo; program status |
| [judge/JUDGE_INPUT_INVESTIGATION_FINDINGS.md](../JUDGE_INPUT_INVESTIGATION_FINDINGS.md) | Close J-1–J-9, J-11, J-12 rows; note J-10 v1 lock |
| [../../README.md](../../README.md) | `judge/waves/` in folder layout if missing |
| [../../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](../../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) | Optional Track link to judge validation |

**Files:** docs listed above

**Deliverable:** All gap rows show Addressed or Locked v1 for J-10.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_review.py tests/unit/test_github_compare_patches.py -q
```

**Human gate:** Staging validation memo signed with dated SQL metrics — LOOP stops here even if unit tests pass.

**Deploy:** Ship with gateway branch merged; staging judge env (`ANTHROPIC_BASE_URL` or `ANTHROPIC_API_KEY`) required for live judge runs.

**Next:** none — program complete; optional `post-finish-gap-pass` before merge.
