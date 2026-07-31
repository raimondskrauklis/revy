# Judge transport reliability — staging validation

**Date:** T0 baseline 2026-07-31 (post-deploy sign-off pending T3)  
**Program:** [waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md](./waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md)  
**Baseline:** [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](./JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md)

## Pre-flight (JT-Q6)

| Check | Expected | Status |
|-------|----------|--------|
| `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` on worker | RTU gateway URL + token | _TBD_ |
| `ANTHROPIC_API_KEY` on worker | Direct Anthropic fallback | _TBD_ |
| `judge_llm_enabled()` | `true` when gateway **or** direct configured | _TBD_ |

## Baseline (T0 — `--since 2026-07-30T08:28:45Z`, post–#71 D0 deploy)

| Metric | Value |
|--------|-------|
| `candidate_runs.runs` | 49 |
| `candidate_runs.with_outcomes` | 28 |
| `candidate_runs.all_failed` | 21 |
| `candidate_runs.skipped_unavailable` | 17 |
| `manifest_candidates.with_parse_error` | 1 |
| Incident `review_run_id` | `019fb6d7-bb98-73e6-9743-1661630be275` |

## After deploy (T3 — fill post T1+T2)

| Metric | Before | After | Notes |
|--------|--------|-------|-------|
| `all_failed` | 21 | _TBD_ | |
| `skipped_unavailable` | 17 | _TBD_ | |
| Worker log: `judge_llm_request_completed` | absent | _TBD_ | T3.3 |
| Smoke gateway + direct | — | _TBD_ | T3.1 |

## Smoke matrix (T3.1)

| Path | Result | Notes |
|------|--------|-------|
| Gateway (RTU) | _TBD_ | |
| Direct | _TBD_ | |

## Live run (T3.3)

| Field | Value |
|-------|-------|
| `head_sha` | _TBD_ |
| `review_run_id` | _TBD_ |
| Log snippet | _TBD_ |
| `judge_status` | _TBD_ |

## Sign-off

- [ ] T3.1 smoke PASS (or partial PASS — direct only if RTU down)
- [ ] T3.2 metrics trend documented
- [ ] T3.3 worker tail shows profile + outcome
- [ ] Program PASS / FAIL: _TBD_
