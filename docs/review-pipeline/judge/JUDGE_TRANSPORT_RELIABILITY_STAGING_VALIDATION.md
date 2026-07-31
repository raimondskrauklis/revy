# Judge transport reliability — staging validation

**Date:** T0 baseline 2026-07-31; T3 partial sign-off 2026-07-31 (pre-staging deploy)  
**Program:** [waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md](./waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md)  
**PR:** [#75](https://github.com/raimondskrauklis/revy/pull/75) (`feat/judge-transport-reliability`)  
**Baseline:** [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](./JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md)

## Pre-flight (JT-Q6)

| Check | Expected | Status |
|-------|----------|--------|
| `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` on worker | RTU gateway URL + token | _PENDING deploy verify_ |
| `ANTHROPIC_API_KEY` on worker | Direct Anthropic fallback | _PENDING deploy verify_ |
| `judge_llm_enabled()` | `true` when gateway **or** direct configured | _PENDING deploy verify_ |

## Baseline (T0 — `--since 2026-07-30T08:28:45Z`, post–#71 D0 deploy)

| Metric | Value |
|--------|-------|
| `candidate_runs.runs` | 49 |
| `candidate_runs.with_outcomes` | 28 |
| `candidate_runs.all_failed` | 21 |
| `candidate_runs.skipped_unavailable` | 17 |
| `manifest_candidates.with_parse_error` | 1 |
| Incident `review_run_id` | `019fb6d7-bb98-73e6-9743-1661630be275` |

## After deploy (T3 — pre-deploy snapshot; re-run post-merge to staging)

| Metric | Before | After (pre-deploy) | Notes |
|--------|--------|--------------------|-------|
| `all_failed` | 21 | 21 | unchanged until staging worker runs T1+T2 |
| `skipped_unavailable` | 17 | 17 | unchanged pre-deploy |
| Worker log: `judge_llm_request_completed` | absent | _PENDING T3.3_ | requires staging deploy |
| Smoke gateway + direct | — | partial | see below |

## Smoke matrix (T3.1 — operator laptop, 2026-07-31)

| Path | Result | Notes |
|------|--------|-------|
| Gateway (RTU) | **FAIL** | `All connection attempts failed` — RTU down |
| Direct | **SKIP** | `ANTHROPIC_API_KEY` not set in operator `.env` |

**Partial PASS:** RTU unreachable; direct path not exercised locally. Re-run on staging worker after deploy with dual credentials.

## Live run (T3.3)

| Field | Value |
|-------|-------|
| `head_sha` | _PENDING — operator staging review post-deploy_ |
| `review_run_id` | _PENDING_ |
| Log snippet | _PENDING — expect `judge_llm_request_started` + `judge_llm_request_completed`_ |
| `judge_status` | _PENDING_ |

## Sign-off

- [x] T0 manifest root cause locked (JT-Q2)
- [x] T1+T2 unit tests green on branch
- [ ] T3.1 smoke PASS on staging worker (gateway when RTU up + direct)
- [ ] T3.2 metrics trend improved post-deploy
- [ ] T3.3 worker tail shows profile + outcome
- [ ] Program PASS: **PARTIAL** — code ready; staging human gate pending

**Ops note:** Optional `LOG_FORMAT=json` on worker droplet for richer `extra` fields without code changes.
