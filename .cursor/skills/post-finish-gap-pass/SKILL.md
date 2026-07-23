---
name: post-finish-gap-pass
description: >-
  After implementation, before doc-sync: re-read the plan, find gaps vs shipped
  code, fix small items, add corpus pages for methodology holes. Use on last
  phase of phase-execution or when user asks for post-ship gap review.
---

# Post-finish gap pass

**When:** last phase of a track — **after** code subphases, **before** doc-sync / changelog.

**Not:** full plan review (`execution-peer-review`) or stress-test (`devils-advocate`).

---

## Steps

1. Re-read plan folder `*_GENERAL_PLAN.md` + `*_FINDINGS.md` vs what shipped.
2. Grep code + plan folder — drift, skipped deliverables, corners cut.
3. `| Gap | Action |` — fix **small in-scope** now; defer large → README note.
4. Investigator “how/what” gaps → **`corpus-program`** + **`author-corpus`** (or **`author-market-screen-corpus`** for `IND-*-CPV`); new corpus file + manifest — not `docs/` copies.
5. Continue to doc-sync (`create-execution-plan`).

Skip if last phase is doc-only.

**Optional in execution file:** subphase `Pn.x — Post-finish gap review` with deliverable = gap table (+ corpus rows if any).
