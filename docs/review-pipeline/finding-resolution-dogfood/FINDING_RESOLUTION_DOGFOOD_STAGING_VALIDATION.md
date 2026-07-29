# Finding resolution dogfood — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md)

**Status:** **in progress** — P0 pushed (`4830ff7`); P1–P2 committed locally; operator fills rows after dogfood pushes.

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| PSA baseline (reference) | `2026-07-29T11:38:12Z` | P0 metrics smoke only |
| Post-P1 deploy | *(TBD)* | Dogfood push 2 — FR-DG1 |
| Post-P2 deploy | *(TBD)* | Dogfood push 3 — FR-DG2; P3 sign-off metrics |

## Dogfood PR

| PR | Branch | Status |
|----|--------|--------|
| *(TBD)* | `chore/finding-resolution-staging-dogfood` | open |

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce `fr_dogfood` probe | pending |
| 2 | Wire probe (FR-DG1) — after P1 merge + deploy | pending |
| 3 | Remove probe (FR-DG2) — after P2 merge + deploy | pending |
| 4 | Optional regrowth | N/A |

## Pass criteria — FR-DG1 (push 2)

| Check | Pass | Evidence |
|-------|------|----------|
| `denominator_active_prior` ≥ 1 | pending | reconcile `resolution_pass` |
| `transitions_addressed` ≥ 1 | pending | reconcile `resolution_pass` |
| G9 not `n/a` | pending | issue comment |
| `summary_json.resolution.addressed` ≥ 1 | pending | publish job |

## Pass criteria — FR-DG2 (push 3)

| Check | Pass | Evidence |
|-------|------|----------|
| `pr_active_count` shrinks vs push 2 | pending | `summary_json` |
| Stale inline collapsed | pending | GitHub + `github_inline_threads` |
| Group `resolved` + `absent_and_addressed` | pending | DB |

## Results (operator)

| Push | `head_sha` | Notes |
|------|------------|-------|
| 1 | — | pending |

## Track C — closure scope (wave C, `fix/fr-closure-scope-hygiene`)

**Probe branch:** `chore/fr-dg2-track-c-staging` (separate from #67). **Fixture:** `backend/tests/fixtures/fr_dg2_track_c/`.

| Step | Intent | Status | Evidence |
|------|--------|--------|----------|
| C3.0 | Delete-only publish smoke | pending | — |
| C3.1 | Introduce probe + publish | pending | group id / revision id |
| C3.2 | Age cohort (unrelated backend commit) | pending | `last_seen_revision_id` before delete |
| C3.3 | Aged delete sign-off | pending | `state`, `resolution_method`, G9 path-removed line |
| C3.4 | Rename guard (optional) | pending | old-path groups stay active |
| C3.5 | FR-Q13 re-open (optional) | pending | — |

**Deploy boundary (`--since`):** *(TBD — post C1+C2 droplet deploy ISO)*
