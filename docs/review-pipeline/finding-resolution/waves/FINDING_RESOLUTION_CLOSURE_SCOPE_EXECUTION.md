# Finding resolution — closure scope execution (wave C)

**LOOP index** for [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md).  
**Authority:** [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) (rev 3).

**Branch:** `fix/fr-closure-scope-hygiene` (C1+C2). **Evidence PR:** #67 (merge evidence-only; do not fold product fix).

## Locked decisions (all phases)

- CS-Q7: hygiene = **path absent at `revision.head_sha`** (`fetch_repository_file_at_sha` 404); compare `deleted_paths` fast path only.
- CS-Q8: hygiene **deletions only** — not `renamed_from_paths`.
- CS-Q9: Pass 2 widen — pairing cohort **OR** `resolution_status == addressed`.
- CS-Q6: exclude hygiene from `resolution_rate_pct`; visible G9 path-removed line.
- R4: HEAD check `None` → fail closed + manifest visibility (`head_check_failed_count` in C2).
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
| C3 | Staging Track C dogfood | [C3](./FINDING_RESOLUTION_CLOSURE_SCOPE_C3_EXECUTION.md) | `254681f` | probe done — **operator C3.0–C3.3** |
| C4 | Doc sync + gap close | [C4](./FINDING_RESOLUTION_CLOSURE_SCOPE_C4_EXECUTION.md) | `0fa3ae5` | done (FR-DG2 awaits C3 staging) |

**Deploy:** Record droplet job ISO after C2 merge — C3 `--since` boundary.

**Related:** [finding-resolution-dogfood](../../finding-resolution-dogfood/README.md) · [#66](https://github.com/raimondskrauklis/revy/pull/66) · [#67](https://github.com/raimondskrauklis/revy/pull/67)
