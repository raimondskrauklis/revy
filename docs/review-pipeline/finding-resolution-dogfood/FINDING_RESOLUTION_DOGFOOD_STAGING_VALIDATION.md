# Finding resolution dogfood — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md)

**Status:** **Track C complete** — [#68](https://github.com/raimondskrauklis/revy/pull/68) deployed `2026-07-29T21:53:28Z`; [#69](https://github.com/raimondskrauklis/revy/pull/69) C3 **PASS**; [#67](https://github.com/raimondskrauklis/revy/pull/67) closed (evidence-only).

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| PSA baseline (reference) | `2026-07-29T11:38:12Z` | P0 metrics smoke only |
| Post-#66 deploy | `2026-07-29T19:20:33Z` | FR-DG2a reference |
| **Post-#68 deploy (wave C)** | **`2026-07-29T21:53:28Z`** | **Track C C3 metrics (`judge_json_contract_staging_metrics`)** |

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

## Track C — closure scope (wave C, [#68](https://github.com/raimondskrauklis/revy/pull/68) deployed)

**Probe branch:** `chore/fr-dg2-track-c-staging` ([#69](https://github.com/raimondskrauklis/revy/pull/69)). **Fixture:** `backend/tests/fixtures/fr_dg2_track_c/`. **Evidence:** #67 closed (evidence-only).

| Step | Intent | Status | Evidence |
|------|--------|--------|----------|
| C3.0 | Delete-only publish smoke | pending | — |
| C3.1a | Probe publish (MD5) | **FAIL** | Revy rev 2 `6d9a9fe` — 0 publishable findings |
| C3.1 | Probe publish (#67-style snippet) | **PASS** | rev 3 `7d63bd0`; group `019fafe7-938a-7f11-99b1-bb830afffcb4`; revision `019fafe5-c504-7805-920f-9131b7f73ee9`; run `019fafe5-d65e-72c0-b05e-15de100036f9`; `gen=1` / `pr=1` |
| C3.2 | Age cohort (unrelated backend commit) | **PASS** | rev 5 `efc579c`; probe `last_seen` rev 3 `019fafe5-c504-7805-920f-9131b7f73ee9`; `gen=0` / `pr=1` |
| C3.3 | Aged delete sign-off | **PASS** | rev 6 `bdb25a4`; group `resolved` + `absent_and_addressed`; `hygiene_path_removed_count=1`; run `019faff3-28aa-74c8-8812-671142ce9eef`; Revy **Closed as path removed: 1**; `pr_active=1` (memo meta finding — probe cohort PASS per VAL8) |
| C3.4 | Rename guard (optional) | skipped | — |
| C3.5 | FR-Q13 re-open (optional) | skipped | — |

**Deploy boundary (`--since`):** `2026-07-29T21:53:28Z` (post-#68 droplet deploy)
