# Finding resolution — post–wave C execution (LOOP index)

**LOOP index** for [FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md](../FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md).  
**Authority:** [FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md](../FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md).

**Branch:** `main` post–#68/#69/#70. **D1 dogfood:** `chore/fr-cs4-structural-fix-staging`.

## Locked decisions (all phases)

- PW-Q5: **M0** and **D0** separate PRs — never mix Moonshot prompt with Pass 3 widen.
- PW-Q4: Pass 3 widen only — **no** Pass 1a `patch_touches_line_region` loosening.
- CS-Q10: Pass 3 for ambiguous `still_open` — **not** file deletion hygiene.
- Dogfood pushes: **backend only** (VAL8); one push per Revy cycle.
- D2: **optional** — human gate; default skip.

## Gap status (update each phase)

| Gap | Closes | Status |
|-----|--------|--------|
| MR-DG1 | M0 | **closed PASS** — [#70](https://github.com/raimondskrauklis/revy/pull/70) |
| FR-CS4 | D1 PASS | defer — wave D (flip in **D3**) |
| FR-CS8 | D2 (optional) / monitor | defer (flip in **D3** if D2 skipped) |

## Execution (LOOP order)

| Phase | Focus | File | Commit | Status |
|-------|--------|------|--------|--------|
| M0 | MR-DG1 Moonshot prompt | [M0](./FINDING_RESOLUTION_POST_WAVE_C_M0_EXECUTION.md) | [#70](https://github.com/raimondskrauklis/revy/pull/70) | **done** |
| D0 | Pass 3 cohort widen | [D0](./FINDING_RESOLUTION_POST_WAVE_C_D0_EXECUTION.md) | — | **done** |
| D1 | FR-CS4 staging dogfood | [D1](./FINDING_RESOLUTION_POST_WAVE_C_D1_EXECUTION.md) | — | pending |
| D2 | FR-CS8 observability (optional) | [D2](./FINDING_RESOLUTION_POST_WAVE_C_D2_EXECUTION.md) | — | optional |
| D3 | Doc sync | [D3](./FINDING_RESOLUTION_POST_WAVE_C_D3_EXECUTION.md) | — | pending |

**Related:** [dogfood P4 (superseded by M0)](../finding-resolution-dogfood/waves/FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md) · [closure scope execution](./FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md)
