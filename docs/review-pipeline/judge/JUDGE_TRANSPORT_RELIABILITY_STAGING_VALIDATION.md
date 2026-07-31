# Judge transport reliability — staging validation

**Date:** T0 baseline 2026-07-31; program **closed partial PASS** 2026-07-31  
**Program:** [waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md](./waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md)  
**Shipped:** [#75](https://github.com/raimondskrauklis/revy/pull/75) merged `1c416a0`  
**Probe (evidence-only):** [#76](https://github.com/raimondskrauklis/revy/pull/76) closed — not merged  
**Baseline:** [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](./JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md)

## Program verdict

| Outcome | Rationale |
|---------|-----------|
| **CLOSED — partial PASS** | Original incident fixed: direct judge does billable inference, T1 transport logs visible, publish no longer withheld on valid judge path. Gateway→direct fallback coded (T2) but not staging-proven — blocked on JT-Q6 dual creds + RTU down. Acceptable to close; re-open only if RTU-up regression. |

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| Post–#71 D0 (T0 baseline) | `2026-07-30T08:28:45Z` | T0 metrics |
| **Post–#75 deploy (T3)** | **`2026-07-31T12:18:17Z`** | **T3.2 metrics (deferred) + probe cohort** |

Deploy job: [Actions run 30629850807](https://github.com/raimondskrauklis/revy/actions/runs/30629850807) — completed `2026-07-31T12:18:17Z`.

## Pre-flight (JT-Q6)

| Check | Expected | Status |
|-------|----------|--------|
| `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` on worker | RTU gateway URL + token | **NOT OBSERVED** — probe run had no `llm.ai.rtu.lv` line |
| `ANTHROPIC_API_KEY` on worker | Direct Anthropic fallback | **PASS** — `api.anthropic.com` 200 ~3.7s; `revy-judge` key **US$0.37** (Jul 26–31) |
| `judge_llm_enabled()` | `true` when gateway **or** direct configured | **PASS** (inferred) — judge ran on probe PR |

## T3 probe PR (evidence-only — [#76](https://github.com/raimondskrauklis/revy/pull/76) closed, not merged)

**Fixture:** `jt_transport_staging_probe.py` on branch `chore/judge-transport-staging-probe` (intentional shell-injection — do not ship).

| Push | Intent | Status |
|------|--------|--------|
| 1 | Judge-eligible probe for E2E + transport verification | **PASS** |

| Check | Pass | Evidence |
|-------|------|----------|
| ≥1 publishable finding on probe file | **PASS** | [Revy comment](https://github.com/raimondskrauklis/revy/pull/76#issuecomment-5142824013) — `critical`/`security` |
| Judge transport logs | **PASS** | `misc/log.txt` L61–63 — `judge_llm_request_started` / `completed` |
| Billable inference | **PASS** | ~3.7s `api.anthropic.com` 200; `revy-judge` US$0.37 |
| Publish not withheld | **PASS** | `github_publish_complete`; no `judge_candidate_unpublished_missing_outcome` |

**Cohort (PR #76 rev 1, `8120cc3`):**

| Field | Value |
|-------|-------|
| `head_sha` | `8120cc3148ab024ec5cddbe26beb0dc175daee7a` |
| Transport `profile` | **direct only** — no `judge_llm_profile_fallback` |
| vs T0 incident | T0: ~5ms, $0 billing, `skipped_unavailable`. T3: ~3.7s, billable, publish OK |

## Baseline (T0 — `--since 2026-07-30T08:28:45Z`)

| Metric | Value |
|--------|-------|
| `candidate_runs.all_failed` | 21 |
| `candidate_runs.skipped_unavailable` | 17 |
| Incident `review_run_id` | `019fb6d7-bb98-73e6-9743-1661630be275` |

## After deploy (T3)

| Metric | T0 | Post-deploy | Notes |
|--------|-----|-------------|-------|
| `judge_llm_request_completed` in worker tail | absent | **present** | probe #76 |
| Direct judge path | broken (T0) | **PASS** | logs + billing |
| Gateway + fallback | untested | **deferred** | JT-Q6 ops when RTU up |

## Smoke matrix (T3.1)

| Path | Laptop | Staging (probe E2E) |
|------|--------|---------------------|
| Gateway (RTU) | FAIL — RTU down | NOT EXERCISED |
| Direct | SKIP | **PASS** |

## Sign-off

- [x] T0 manifest root cause locked (JT-Q2)
- [x] T1+T2 shipped ([#75](https://github.com/raimondskrauklis/revy/pull/75))
- [x] T3.3 live run — direct path + T1 logging + billing
- [ ] T3.1 droplet smoke — **deferred** (RTU down + gateway creds not on worker)
- [ ] T3.2 post-deploy metrics — **deferred** (optional trend check)
- [x] **Program CLOSED — partial PASS** (2026-07-31)

**Follow-up (ops, not code):** Set `ANTHROPIC_BASE_URL`+token on droplet; when RTU returns run `test_anthropic_judge_gateway --compare-direct` to confirm `judge_llm_profile_fallback`.
