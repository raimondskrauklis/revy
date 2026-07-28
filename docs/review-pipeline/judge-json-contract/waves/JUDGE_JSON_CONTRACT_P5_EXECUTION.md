# Judge JSON contract P5 — Staging validation & doc sync (execution)

Phase **P5** of [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](../JUDGE_JSON_CONTRACT_GENERAL_PLAN.md). **P5 only — final phase.**

**Goal:** Human gate proving ≥95% judge candidate → outcome row on dogfood PRs; program docs marked shipped.

## Decisions locked for P5

- Validation memo: `JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md` in program folder.
- Success metrics: outcome persistence rate, prompt p50, RG-6 `judge_candidate_unpublished_missing_outcome` rate, compare to findings baseline (13/15 failed).
- SQL repro links to [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](../../finding-resolution/FINDING_RESOLUTION_TECHNICAL_FINDINGS.md).
- No production sign-off; no program tag.
- `changelog.json` — skip (backend-only wave, no user-facing UI).

## Out of scope for P5

- Moonshot parse_report changes
- Finding-resolution closure retest (separate memo)

---

## P5.1 — Staging dogfood judge runs

**What:** On staging PR with escalation finding: trigger reconcile+judge; record before/after outcome persistence and prompt sizes from manifest.

**Files:** manual — staging Revy + GitHub PR

**Deliverable (non-gate):** Before/after table in validation memo.

---

## P5.2 — RG-6 warning rate check

**What:** Confirm `judge_candidate_unpublished_missing_outcome` warnings rare and only on genuine policy withhold — not parse noise.

**Files:** `JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md`, `backend/app/services/github_publish.py` (reference only)

**Deliverable:** Memo § RG-6 with sample log/manifest IDs.

---

## P5.3 — Validation memo

**What:** Create `docs/review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md` — dated results, SQL repro, P0 matrix final, P4 skip note if applicable.

**Files:** `docs/review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md`

**Deliverable:** Memo file exists with dated results table.

---

## P5.4 — Doc sync

**What:** Close program docs; link validation memo; update recovery checklist and review-pipeline index.

| Doc | Change |
|-----|--------|
| [waves/JUDGE_JSON_CONTRACT_EXECUTION.md](./JUDGE_JSON_CONTRACT_EXECUTION.md) | Status Done + commit sha per phase row |
| [README.md](../README.md) | Program status shipped; link validation memo |
| [JUDGE_JSON_CONTRACT_FINDINGS.md](../JUDGE_JSON_CONTRACT_FINDINGS.md) | Close JC-* gaps; update staging metrics |
| [../../README.md](../../README.md) | Add `judge-json-contract/` to folder layout |
| [../../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](../../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) | Mark judge-json-contract track complete |

**Files:** docs listed above

**Deliverable:** JC gap registry rows show Addressed for G1–G8.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_github_finding_judge.py tests/unit/test_github_finding_closure.py tests/unit/test_github_pipeline_trace.py -q
```

**Human gate:** Staging validation memo signed with ≥95% outcome persistence on dogfood PR — LOOP stops here even if tests pass.

**Next:** none — program complete after merge to `main`.
