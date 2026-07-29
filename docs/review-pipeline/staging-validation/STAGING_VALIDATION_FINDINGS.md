# Staging validation — findings

**Date:** 2026-07-29  
**Purpose:** Baseline for a **repeatable operator workflow** — post-deploy dogfood PRs, deploy-boundary metrics windows, parallel program tracks, and evidence tables. **No execution steps.**

**Trigger:** PSA #62 merged; RCX pass 2 + PSA dogfood started same session; PR #62 rev 4–5 runs were **pre-deploy** and polluted validation evidence.

**Evidence:** Deploy workflow `30448037218` (PSA #62, deploy finished `2026-07-29T11:38:12Z`); staging DB review runs; `judge_json_contract_staging_metrics.py` pass 2 output; [PSA validation memo](../publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md); [RCX validation memo](../review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md); dogfood PR [#63](https://github.com/raimondskrauklis/revy/pull/63).

---

## Build principles

1. **Deploy boundary is sacred** — metrics and pass/fail tables use `--since` = deploy job completion ISO; runs before that window are **excluded** from program sign-off (may be noted as historical only).
2. **Dogfood PR ≠ feature PR** — validation uses `chore/<program>-staging-dogfood` (or `chore/staging-validation-<track>`) with minimal `backend/**` touch to autostart; never sign off on the merged feature PR's pre-deploy runs alone.
3. **Parallel tracks, isolated memos** — RCX, PSA, judge-json, finding-resolution each keep their own `*_STAGING_VALIDATION.md`; this program defines the **shared operator loop** only.
4. **Script first, GitHub second** — run `judge_json_contract_staging_metrics.py` (and future extensions) before filling tables; GitHub issue-comment inspection confirms surface behavior.
5. **Growing metrics history** — as deploy frequency increases, multiple `--since` windows coexist; never overwrite a prior pass table — add pass N sections.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Deploy boundary** | Timestamp when `Build, Push, and Deploy to Droplet` job completes on `main` after merge |
| **Validation PR** | Short-lived chore PR opened **after** deploy to exercise staging worker on new code |
| **Pass N** | One validation cycle bounded by a deploy `--since` (RCX pass 1 = post-#60, pass 2 = post-#61, etc.) |
| **Parallel track** | Independent program validation memo filled in the same calendar window without blocking others |
| **INCONCLUSIVE gate** | Metrics script reports 0 completed runs in window — dogfood PR not yet reviewed |

---

## What exists vs genuinely new

### Shipped (verified)

| Asset | Location | Notes |
|-------|----------|-------|
| Per-program staging memos | `docs/review-pipeline/*/*_STAGING_VALIDATION.md` | PSA, RCX, judge-json, finding-resolution |
| Shared metrics script | `backend/scripts/judge_json_contract_staging_metrics.py` | Judge + retrieve manifest + `context_stats` + `--rcx-gate` |
| RCX pass 1 + pass 2 filled | [RCX memo](../review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md) | Pass 2 `--since 2026-07-29T10:52:38Z` → **PASS** |
| PSA memo stub (in progress) | [PSA memo](../publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md) | Deploy row filled; post-deploy window `11:38:12Z` |
| Autostart on `backend/**` PRs | R8 on `main` | Dogfood PR triggers review without `@revy review` |
| Staging DB evidence | `github_review_runs`, `github_publish_jobs.summary_json`, `context_stats` | Queryable via `PRODUCTION_DATABASE_URL` in `backend/.env` |
| Deploy on `main` push | `.github/workflows/deploy.yml` | Droplet deploy job provides deploy-boundary timestamp |

### Genuinely new (this program)

| Capability | Why new |
|------------|---------|
| **Meta workflow doc** | No single place describing chore dogfood PR pattern + deploy boundary rule |
| **Validation PR naming convention** | Ad hoc (`chore/psa-staging-dogfood` invented 2026-07-29) |
| **Multi-pass table discipline** | RCX has pass 1/2; PSA lacks pass numbering; no index of active dogfood PRs |
| **PSA-specific metrics in script** | `summary_json.generation_active_count` / two-block surface not in metrics script yet |
| **Parallel track dashboard** | Operator must open 3+ memos to see overall staging health |
| **Pre-deploy exclusion rule** | Not documented until PSA #62 lesson (rev 4–5 showed legacy `### Findings table`) |

### Reuse traps

| Trap | Detail |
|------|--------|
| **Feature PR runs = sign-off** | PR #62 reviews at 11:20–11:33Z ran **before** PSA deploy — issue comment still RCX-era shape |
| **`--since` merge time vs deploy time** | Merge `11:33:37Z` ≠ worker ready `11:38:12Z` — use deploy job completion |
| **0 runs = PASS** | `--rcx-gate` with empty window returns INCONCLUSIVE checks but `passed: true` — document operator interpretation |
| **Single comment ID across revisions** | Issue comment updated in place — validate `head_sha` in metadata, not comment count |
| **Parallel tracks blocking** | PSA P2 execution says RCX/judge-json parallel — validation program should reinforce non-blocking |

---

## Incident — PSA #62 pre-deploy evidence (2026-07-29)

| Run (UTC) | PR | `head_sha` | Worker code | Issue comment shape | Count for PSA? |
|-----------|-----|------------|-------------|---------------------|----------------|
| 11:12:28 | #62 | `826923d3` | pre-PSA | no publish / RCX inject only | **no** |
| 11:20:48 | #62 | `b8e5342` | pre-PSA | `### Findings table` (legacy) | **no** |
| 11:33:09 | #62 | `56963dc` | pre-PSA | `### Findings table` (legacy) | **no** |
| ≥ 11:38:12 | — | — | PSA on staging | — | **first eligible window** |

**Lesson (locked):** Program P2 staging sign-off requires ≥1 completed run with `created_at >= deploy_boundary` on a **validation PR** or explicit post-deploy push.

---

## Catalog — operator loop (target)

```text
merge feature PR → main
        │
        ▼
deploy job completes → record ISO (deploy_boundary)
        │
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
  metrics --since     open chore          fill per-program
  (shared script)     dogfood PR          memo pass table
        │                  │                  │
        └──────────────────┴──────────────────┘
                           ▼
              3-push dogfood (optional per program)
                           ▼
              operator sign-off row in memo
```

---

## Parallel tracks (2026-07-29 snapshot)

| Track | Deploy boundary | Metrics window | Gate | Dogfood PR | Memo status |
|-------|-----------------|----------------|------|------------|-------------|
| RCX pass 2 | #61 `10:52:38Z` | `--since 2026-07-29T10:52:38Z` | `--rcx-gate` **PASS** | PR #61 (historical) | **filled** |
| PSA post-#62 | #62 `11:38:12Z` | `--since 2026-07-29T11:38:12Z` | 0 runs INCONCLUSIVE | **PR #63** open | **in progress** |
| Judge JSON | prior | per JC memo | unchanged | — | not this session |

---

## SV-Q registry (locked / open)

| ID | Question | Status | Decision / notes |
|----|----------|--------|------------------|
| SV-Q1 | Meta program vs ops runbook only? | **locked** | Dedicated `staging-validation/` program folder — findings first |
| SV-Q2 | Dogfood branch naming? | **locked** | `chore/<program>-staging-dogfood` (e.g. `chore/psa-staging-dogfood`) |
| SV-Q3 | Minimal touch to autostart? | **locked** | `backend/**` change — test module docstring or noop test touch acceptable |
| SV-Q4 | Deploy boundary source of truth? | **locked** | GitHub Actions deploy job `completedAt` on `main`, not merge timestamp |
| SV-Q5 | Exclude pre-deploy feature PR runs? | **locked** | Yes — note in memo § Pre-deploy note; do not mark pass criteria |
| SV-Q6 | Shared script vs per-program scripts? | **open** | Extend `judge_json_contract_staging_metrics.py` with `--psa-gate` vs new script |
| SV-Q7 | Validation PR merges to `main`? | **open** | Prefer close without merge after sign-off; or merge doc-only memo updates only |
| SV-Q8 | CI hook for metrics drift? | **open** | Defer — `SKIP_CI_TESTS` still true; operator runs locally |
| SV-Q9 | Multi-program single dogfood PR? | **open** | One PR can touch backend once; multiple memos filled from same runs when criteria overlap |
| SV-Q10 | Index of active validation PRs? | **locked** | `staging-validation/README.md` § Active dogfood PRs |

---

## Gaps registry (SV-G*)

| ID | Gap | Severity | Target phase |
|----|-----|----------|--------------|
| SV-G1 | No meta workflow doc | high | findings (this doc) ✓ |
| SV-G2 | PSA metrics not in shared script (`generation_active_count`, two-block probe) | medium | general plan P0 |
| SV-G3 | No standard 3-push dogfood checklist template in repo | medium | general plan |
| SV-G4 | Recovery checklist lacks validation PR track | low | doc cross-link |
| SV-G5 | `SKIP_CI_TESTS` — metrics never CI-gated | medium | ops / separate |
| SV-G6 | Pre-deploy vs post-deploy not in per-program P2 execution templates | medium | cross-link from create-execution-plan |

---

## Script reference (operator)

```bash
# RCX / retrieve / context_stats (shared)
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics \
     --since <DEPLOY_ISO> --rcx-gate --json' \
  | tee /tmp/staging-metrics.json

# Greptile SSOT drift (on program switch commits)
pipenv run python -m scripts.generate_greptile_files_from_review_context --check
pipenv run pytest tests/unit/test_generate_greptile_files.py -q
```

**Staging DB:** `PRODUCTION_DATABASE_URL` in `backend/.env` (not `DATABASE_URL` asyncpg DSN).

---

## Devil's advocate

- **Chore PR noise** — many open validation PRs clutter GitHub; index + close-after-sign-off policy required (SV-Q7).
- **False confidence from script PASS** — RCX gate can PASS with 1 inject run while PSA surface untested — parallel memos must stay independent.
- **Dogfood on self-repo** — Revy reviewing Revy may not match customer repos; still valuable for pipeline contract.
- **Metrics script name** — `judge_json_contract_*` undersells RCX/retrieve scope; rename is cosmetic debt.

---

## Next artifacts (not in scope for findings)

1. `STAGING_VALIDATION_DISCUSSION.md` — lock SV-Q6–Q9 after PSA #63 dogfood completes.
2. `STAGING_VALIDATION_GENERAL_PLAN.md` — script extensions, memo template, optional validation PR bot comment parser.
3. Cross-links from [recovery checklist](../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) Track F and per-program P2 execution files.
