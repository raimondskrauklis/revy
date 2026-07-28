# Finding resolution P5 — Staging gate & doc sync (execution)

Phase **P5** of [FINDING_RESOLUTION_GENERAL_PLAN.md](../FINDING_RESOLUTION_GENERAL_PLAN.md). **P5 only — final phase.**

**Goal:** Staging proof of resolution rate + closure on real PR; program docs marked shipped.

## Decisions locked for P5

- Validation memo: `FINDING_RESOLUTION_STAGING_VALIDATION.md` in program folder.
- Dogfood: fix → push → metrics on issue comment → thread resolve (Option A).
- Row for compare API failure → no false `addressed` closure.
- No production sign-off; no program tag.
- `changelog.json` — only if **P4.5** shipped visible reviewer resolution badges to end users; otherwise skip.

## Out of scope for P5

- FR-Q10 post-merge batch
- Workspace policy rules

---

## P5.1 — Staging dogfood run

**What:** On staging PR with known ERROR inline: (1) record metrics before fix; (2) push fix; (3) record after publish — resolution rate, addressed count, thread state.

**Files:** manual — staging Revy + GitHub PR

**Deliverable (non-gate):** Before/after table in validation memo.

---

## P5.2 — Compare-failure checklist row

**What:** Document or simulate compare failure path (staging or unit fixture reference) — groups stay `still_open`, `closure_blocked_reason=compare_failed`.

**Files:** `FINDING_RESOLUTION_STAGING_VALIDATION.md`

**Deliverable:** Memo § compare failure with expected behavior.

---

## P5.3 — Validation memo

**What:** Create `docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_STAGING_VALIDATION.md` — dated results, metrics table, verification judge sample (if any).

**Files:** `docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_STAGING_VALIDATION.md`

**Deliverable:** Memo file exists with dated results.

---

## P5.4 — Doc sync

**What:** Close program docs; link validation memo; update recovery checklist.

| Doc | Change |
|-----|--------|
| [waves/FINDING_RESOLUTION_EXECUTION.md](./FINDING_RESOLUTION_EXECUTION.md) | Status Done + commit sha per phase row |
| [README.md](../README.md) | Program status shipped; link validation memo |
| [FINDING_RESOLUTION_FINDINGS.md](../FINDING_RESOLUTION_FINDINGS.md) | Close FR-Q gaps addressed in ship |
| [../../README.md](../../README.md) | `finding-resolution/waves/` in folder layout if missing |
| [../../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](../../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) | Track link to finding-resolution validation |

**Files:** docs listed above

**Deliverable:** FR-Q registry rows show Addressed or Locked v1 for deferred items.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_closure.py tests/unit/test_github_resolution_metrics.py tests/unit/test_github_publish_formatter.py -q
```

**Human gate:** Staging validation memo signed with real PR evidence — LOOP stops here even if tests pass.

**Next:** none — program complete after merge to `main`.
