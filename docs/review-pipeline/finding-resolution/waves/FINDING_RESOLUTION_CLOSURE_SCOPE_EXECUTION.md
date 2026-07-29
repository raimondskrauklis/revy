# Finding resolution — closure scope execution (wave C)

**LOOP index** for [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md).  
**Authority:** [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) (rev 3).

**Branch:** `main` (product [#68](https://github.com/raimondskrauklis/revy/pull/68) merged `162d7e7`). **Dogfood:** `chore/fr-dg2-track-c-staging`. **Evidence:** #67 closed.

## Locked decisions (all phases)

- CS-Q7: hygiene = **path absent at `revision.head_sha`** (`fetch_repository_file_at_sha` 404); compare `deleted_paths` fast path only.
- CS-Q8: hygiene **deletions only** — not `renamed_from_paths`.
- CS-Q9: Pass 2 widen — pairing cohort **OR** `resolution_status == addressed`.
- CS-Q11: Pass 1a **`deleted_paths` only** — not rename `previous_filename` (R1).
- CS-Q6: exclude hygiene from `resolution_rate_pct`; visible G9 path-removed line.
- R4: HEAD check `None` → `head_check_failed`; compare fail + path gone → `compare_failed` (no hygiene stamp); manifest `head_check_failed_count`.
- E2E test mandatory: sync → Pass 2 on **aged** cohort (not resolver unit alone).

## Gap status (update each phase)

| Gap | Closes | Status |
|-----|--------|--------|
| FR-CS1 | C3 PASS | closed (code) — staging pending |
| FR-CS6 | C3 PASS | closed (code) — staging pending |
| FR-CS7 | C3 PASS | closed (code) — staging pending |
| FR-CS3 | C2 PASS | closed (`d4666aa`) |
| FR-DG2 | C3 PASS | partial PASS — staging pending |
| FR-CS4 | — | defer |
| FR-CS8 | — | defer |

## Execution (LOOP order)

| Phase | Focus | File | Commit | Status |
|-------|--------|------|--------|--------|
| C0 | SSOT, Greptile, Bugbot, index | [C0](./FINDING_RESOLUTION_CLOSURE_SCOPE_C0_EXECUTION.md) | `c7c84f1` | done |
| C1 | HEAD hygiene + Pass 2 widen | [C1](./FINDING_RESOLUTION_CLOSURE_SCOPE_C1_EXECUTION.md) | `d4666aa` | done |
| C2 | Manifest + G9 | [C2](./FINDING_RESOLUTION_CLOSURE_SCOPE_C2_EXECUTION.md) | `d4666aa` | done |
| C3 | Staging Track C dogfood | [C3](./FINDING_RESOLUTION_CLOSURE_SCOPE_C3_EXECUTION.md) | — | **in progress** — [#69](https://github.com/raimondskrauklis/revy/pull/69) |
| C4 | Doc sync + gap close | [C4](./FINDING_RESOLUTION_CLOSURE_SCOPE_C4_EXECUTION.md) | `0fa3ae5` | pending C3 PASS |
| — | Post–#68 Revy fixes | findings § Post–#68 | `0277f4d` | done (shipped in #68) |

**Deploy:** `2026-07-29T21:53:28Z` — C3 `--since` boundary.

**Related:** [finding-resolution-dogfood](../../finding-resolution-dogfood/README.md) · [#66](https://github.com/raimondskrauklis/revy/pull/66) · [#67](https://github.com/raimondskrauklis/revy/pull/67) · [#68](https://github.com/raimondskrauklis/revy/pull/68)
