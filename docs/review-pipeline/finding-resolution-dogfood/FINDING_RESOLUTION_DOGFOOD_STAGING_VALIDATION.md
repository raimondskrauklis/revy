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

## Wave D — FR-CS4 structural fix (post–#71)

**Probe PR:** [#72](https://github.com/raimondskrauklis/revy/pull/72) · **Branch:** `chore/fr-cs4-structural-fix-staging` · **Fixture:** `backend/app/services/fr_cs4_staging_probe.py` (attempt 5+; was `app/dogfood/`, was `tests/fixtures/`). **D0:** [#71](https://github.com/raimondskrauklis/revy/pull/71) deployed `2026-07-30T08:28:45Z`.

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| **Post-#71 deploy (D0)** | **`2026-07-30T08:28:45Z`** | D1 metrics (`judge_json_contract_staging_metrics`) |

### Pre-flight (before push 1)

| Check | Status | Evidence |
|-------|--------|----------|
| `judge_llm_enabled()` on `revy-worker` | **PASS** | `judge_llm_enabled: True`; `effective_judge_provider: anthropic` (operator 2026-07-30) |

### Push 1 — introduce probe (D1.1)

| Attempt | `head_sha` | Revy rev | Status | Evidence |
|---------|------------|----------|--------|----------|
| **1** | `0bcfc81` | 1 | **FAIL** | Revy check PASS; **0 publishable findings**; comment [5128728008](https://github.com/raimondskrauklis/revy/pull/72#issuecomment-5128728008) — `format_summary_comment` kwargs (post-M0 silent) |
| **2** | `afdfeca` | 2 | **FAIL** | Revy check PASS; **0 publishable findings**; bare `except` defect (D1-O1) — still silent |
| **3** | `7f2b357` | 3 | **FAIL** (probe) | 2 publishable — **doc path drift only** (`D1_FINDINGS.md`, `D1_GENERAL_PLAN.md`); **0 findings on `app/dogfood/fr_cs4_probe.py`** |
| **4** | `ce2b547` | 4 | **FAIL** (probe) | 0 new publishable; 1 prior doc finding closed; **1 doc finding still open**; probe silent |
| **5** | `71feceb` | 5 | **FAIL** (probe) | Revy skipped/0 probe findings (DB: no rows for `71feceb` sha — superseded by rev 6) |
| **6** | `3754315` | 6 | **PARTIAL** | `warning`/`maintainability` — not Pass 3 eligible |
| **7** | `ff89066` | 7 | **PASS** | Judge-eligible probe group — see cohort row below |

**FR-CS4 cohort (rev 7 — use for push 2 / D1.3):**

| Field | Value |
|-------|-------|
| `head_sha` | `ff89066c2a657817ff13af6e51dce291672d859e` |
| `group_id` | `019fb461-00d4-75f5-b27e-d9a0a1b77536` |
| `last_seen_revision_id` | `019fb45c-c4a7-7ac8-b118-2abf049c82ea` |
| `review_run_id` | `019fb45c-e935-7f71-a3ba-4d246633af18` |
| `start_line` / `end_line` | `16` / `16` |
| `fingerprint` | `27c16742932165d08ca72896bbdf7d37bc09ae93d0d1bd08e0aa752362f29b48` |
| `severity` / `category` | `critical` / `security` |
| `judge_status` | `completed` (`judge_escalation_candidate_count=2`) |

**Rev 6 partial (wrong cohort):** `019fb43d-59eb-7554-96f0-ef889aa06277` — `warning`/`maintainability`; superseded on rev 7.

#### Root cause (attempt 1)

| Hypothesis | Likelihood | Notes |
|------------|------------|-------|
| **Post-M0 kwargs pattern neutralized** | **high** | Probe uses `format_summary_comment(groups=[])`. **M0 [#70](https://github.com/raimondskrauklis/revy/pull/70)** taught Moonshot the real formatter API; Track C C3.1 **PASS** used the same kwargs shape **before** M0 merged. |
| Discovery judge pre-publish dismiss | medium | Check staging `github_finding_judge_outcomes` for discovery rows on rev 1 — may explain 0 publishable without Moonshot silence. |
| `tests/fixtures/` path deprioritized | low | Track C and #67 used same path family; C3.1 published from `fr_dg2_track_c/`. |
| Reachable vs `if False:` dead code | low | Attempt 1 used reachable call chain; unlikely sole cause vs post-M0 API context. |
| Doc-heavy PR steals findings | **high** (rev 3) | Rev 3 published 2 doc maintainability warnings; probe code silent — avoid doc churn in probe pushes. |
| Judge-gated probe defects dismissed | **high** (rev 4) | Error/security in `app/dogfood/` unpublished; maintainability in `app/services/` publishes but **not Pass 3 eligible** (rev 6). |

**Do not proceed to push 2** until attempt 2 yields ≥1 publishable finding with anchored lines recorded (D1 findings edge case).

#### Proceed options (operator + implementer)

| ID | Option | Action | Pros | Cons | Verdict |
|----|--------|--------|------|------|---------|
| **D1-O1** | **Revise defect class** | Replace `format_summary_comment` misuse with non-formatter bug | Attempt 2 **FAIL** — bare `except` also 0 publishable | **Done** — insufficient alone |
| **D1-O11** | Move to `app/services/` + logic defect | `fr_cs4_staging_probe.py` divide-by-zero | Rev 6 published group — **wrong severity** for Pass 3 | **Done** — partial |
| **D1-O12** | Judge-eligible probe defect | `error`/`security` on anchored lines in `app/services/`; discovery judge must uphold | Enables Pass 3 `verification_dismissed` | **Proceed** (attempt 6) |
| **D1-O5** | `@revy review` retry without code change | Comment on PR | Zero cost | Attempt 1 already clean PASS with 0 gen; **very low yield** | **Reject** |
| **D1-O6** | Merge #72 and dogfood on `main` | Merge before publish | — | Push 1 already ran on PR head; merge does not retroactively create findings | **Reject** |
| **D1-O7** | DB-only investigation first | Query rev 1 run for suppressed/dismissed findings before revising probe | Confirms judge-dismiss vs Moonshot silence | Does not unblock D1 alone | **Do in parallel** with D1-O1 |

**Recommended path:** **D1-O12** — revise anchored defect to judge-eligible class (`error`+`bug` or `security`); backend-only commit; confirm DB row has `severity`/`category` before push 2. Rev 6 group is **not** the FR-CS4 cohort.

**Staging DB checks (D1-O7) — executed 2026-07-30:**

```bash
cd backend && DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics --since 2026-07-30T08:28:45Z --json
```

Rev 6 probe query (representative):

```sql
SELECT g.id, g.fingerprint, g.severity, g.category, g.state, f.start_line, f.end_line
FROM github_finding_groups g
JOIN github_findings f ON f.group_id = g.id
JOIN github_review_runs rr ON rr.id = f.review_run_id
JOIN github_pull_request_revisions rev ON rev.id = rr.revision_id
WHERE rev.head_sha = '3754315dadf9b10939f4813b53e38e74916ad4f5'
  AND g.file_path LIKE '%fr_cs4_staging_probe%';
```

### Push 2 — structural fix outside line region (D1.2)

**Done** — `203239d` / rev 8 (`203239dd4dd82f8d99966f2bd4b3b386090a36ca`).

| Field | Value |
|-------|-------|
| `head_sha` | `203239dd4dd82f8d99966f2bd4b3b386090a36ca` |
| cohort `group_id` | `019fb461-00d4-75f5-b27e-d9a0a1b77536` |
| cohort fingerprint `gen` on rev 8 | **0** (fingerprint `27c16742…` absent from rev 8 run) |
| line-region overlap | **PASS** — diff did not edit lines 16–16 |
| new rev-8 probe group | `019fb6c9-fa81-73e6-a671-6da94c3c5628` (`de13b1e5…`) — Moonshot re-flagged dead `subprocess` body |

### Sign-off (D1.3)

**FAIL** — rev 8 publish (`review_run_id` `019fb6c9-3008-760f-869f-8cbbafffd9ab`).

| Check | Status | Evidence |
|-------|--------|----------|
| Cohort fingerprint `gen=0` on push 2 | **PASS** | No rev-8 finding row for `27c16742…` |
| Cohort `state=resolved` | **FAIL** | `019fb461` → `superseded` (replaced by `019fb6c9`) |
| `resolution_method=verification_dismissed` | **FAIL** | `verification_dismissed: 0` in publish resolution |
| `judge_purpose=verification` outcome | **FAIL** | Only `discovery` outcomes on rev 7–8 |
| `still_open` after push 2 | **FAIL** | `still_open_count: 1`; cohort `resolution_status=still_open` |
| **FR-CS4 staging PASS** | **FAIL** | — |

**Root cause:** Push 2 left anchored `subprocess.call(..., shell=True)` in file (uncalled). Moonshot published a **new** finding (new fingerprint) on rev 8 → superseded cohort `019fb461` before Pass 3 could verify-dismiss. Pass 3 excludes `fingerprints_in_run` for the new group; superseded cohort is ineligible (`state != active`).

**Next (D1-O13):** Probe design must avoid re-reportable dead code on push 2 while keeping anchored hunk unchanged — or accept product gap and document FR-CS4 blocker for D3.

**Implementer handoff:** [FR_CS4_D1_PASS3_HANDOFF.md](./FR_CS4_D1_PASS3_HANDOFF.md) — supersede-before-Pass-3 product gap, code map, success criteria.
