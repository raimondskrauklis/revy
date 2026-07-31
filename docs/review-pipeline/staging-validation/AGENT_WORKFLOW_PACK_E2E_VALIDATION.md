# Agent workflow pack — E2E validation

**Program:** [staging-validation README](./README.md) · **Pack:** `internal-docs/agent-workflow-pack/` (gitignored; not shipped)

**Status:** **E2E push 1 merged** — bootstrap `.agent/` layer + skills audit ([#73](https://github.com/raimondskrauklis/revy/pull/73)).

**Purpose:** Validate portable workflow pack bootstrap, `staging-validation` skill, and ship gate on a real PR (docs-only; no product behavior change).

---

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| Post-#71 deploy (D0 baseline) | `2026-07-30T08:28:48Z` | metrics snapshot below |
| E2E PR merge | `2026-07-31T10:00:44Z` | post-merge sign-off |

**Evidence:** `gh run list --workflow=deploy.yml --branch=main` → run `30526850200` completed `2026-07-30T08:28:48Z`.

---

## Dogfood PR

| PR | Branch | Status |
|----|--------|--------|
| [#73](https://github.com/raimondskrauklis/revy/pull/73) | `chore/agent-workflow-e2e-validation` | merged |

---

## E2E flow checklist (push 1)

| Step | Pass | Evidence |
|------|------|----------|
| Skill audit — 14 existing + 2 new (`bootstrap-workflow`, `staging-validation`) = 16 total | **PASS** | `.agent/manifest.json` → `skills.installed` |
| Materialize `.agent/manifest.json` | **PASS** | `integrations.revy: true`, `greptile: false`, `scopes` backend/frontend |
| Mirror review context — `.revy` canonical → `.agent` mirror | **PASS** | `manifest.review_context.ssot` = `.revy/review-context.json` |
| Flow flags `phase-loop` + `ship` on; `greptile-parallel` off | **PASS** | `.agent/flows/*.json` |
| Copy `skills.catalog.json` | **PASS** | `.agent/skills.catalog.json` |
| Greptile generator `--check` (unchanged SSOT) | **PASS** | `generate_greptile_files_from_review_context --check` exit 0 |
| Staging metrics script (real DB) | **PASS** | see metrics row below |
| Local Bugbot before push | **PASS** | dual-SSOT fixed — `.revy` canonical in manifest |
| `gh pr create` | **PASS** | [#73](https://github.com/raimondskrauklis/revy/pull/73) |

---

## Metrics snapshot (operator — post-#71 window)

**Command:**

```bash
cd backend && DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics --since 2026-07-30T08:28:48Z --json
```

| Metric | Value | Notes |
|--------|-------|-------|
| `database` | `revy-staging` | |
| `alembic_version` | `2026_07_29_1200_0029_review_context_stats` | |
| `candidate_runs.runs` | 47 | in window |
| `outcome_persistence_pct` | 75.0% | |
| `review_context.retrieve_manifest.runs` | 9 | |
| `review_context.retrieve_manifest.diff_truncated_pct` | 0.0% | |

Queried: 2026-07-31 (agent E2E session).

---

## Sign-off (E2E pack)

| Check | Status | Evidence |
|-------|--------|----------|
| Bootstrap materialized without running pack scripts | **PASS** | agent wrote `.agent/*` from templates |
| Greptile not required (off by default) | **PASS** | `integrations.greptile: false` |
| Validation memo filled from real script output | **PASS** | metrics table above |
| **E2E pack push 1** | **PASS** | PR #73 open; Bugbot clean after SSOT fix |

**Next:** merge E2E PR → optional push 2 tests `staging-validation` update row on staging dogfood PR.
