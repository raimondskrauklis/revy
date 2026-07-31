# Judge transport reliability — staging validation

**Date:** T0 baseline 2026-07-31; T3 partial sign-off 2026-07-31 (post–#75 deploy + probe [#76](https://github.com/raimondskrauklis/revy/pull/76))  
**Program:** [waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md](./waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md)  
**PR:** [#75](https://github.com/raimondskrauklis/revy/pull/75) merged `1c416a0`  
**Baseline:** [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](./JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md)

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| Post–#71 D0 (T0 baseline) | `2026-07-30T08:28:45Z` | T0 metrics |
| **Post–#75 deploy (T3)** | **`2026-07-31T12:18:17Z`** | **T3.2 metrics + live probe cohort** |

Deploy job: [Actions run 30629850807](https://github.com/raimondskrauklis/revy/actions/runs/30629850807) — `Build, Push, and Deploy to Droplet` completed `2026-07-31T12:18:17Z`.

## Pre-flight (JT-Q6)

| Check | Expected | Status |
|-------|----------|--------|
| `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` on worker | RTU gateway URL + token | **NOT OBSERVED** — probe run had no `llm.ai.rtu.lv` line; gateway vars likely unset on worker |
| `ANTHROPIC_API_KEY` on worker | Direct Anthropic fallback | **PASS** — `api.anthropic.com` 200 ~3.7s; `revy-judge` key billed **US$0.37** (Jul 26–31, operator 2026-07-31) |
| `judge_llm_enabled()` | `true` when gateway **or** direct configured | **PASS** (inferred) — judge ran on probe PR |

## T3 probe PR (live judge + transport)

**PR:** [#76](https://github.com/raimondskrauklis/revy/pull/76) · **Branch:** `chore/judge-transport-staging-probe` · **Fixture:** `backend/app/services/jt_transport_staging_probe.py`

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce judge-eligible probe (`critical`/`security` shell injection) | **PASS** |

**Pass criteria (push 1):**

| Check | Pass | Evidence |
|-------|------|----------|
| ≥1 publishable finding on probe file | **PASS** | Revy rev 1 — `critical`/`security` on probe file; [issue comment](https://github.com/raimondskrauklis/revy/pull/76#issuecomment-5142824013) 2026-07-31T12:24:19Z |
| `judge_escalation_candidate_count` ≥ 1 | **PASS** (inferred) | Judge HTTP + reconcile + publish completed (no `judge_candidate_unpublished_missing_outcome`) |
| Worker: `judge_llm_request_started` + `judge_llm_request_completed` | **PASS** | `misc/log.txt` L61–63 |
| `judge_status` = `completed` (not `skipped_unavailable`) | **PASS** (inferred) | Publish succeeded; no `github_finding_judge_failed` |
| Outcome row persisted | **PASS** (inferred) | RG-6 gate passed — publish completed |

### Operator protocol — parallel flow + behavior

| Track | What | Status |
|-------|------|--------|
| **A — E2E flow** | Probe PR #76 staging review | **PASS** — see cohort + live run below |
| **B — Transport behavior** | `test_anthropic_judge_gateway --compare-direct` on droplet | _PENDING_ |
| **C — Metrics** | `judge_json_contract_staging_metrics --since 2026-07-31T12:18:17Z` | _PENDING_ |

**Cohort row (push 1 — PR #76 rev 1):**

| Field | Value |
|-------|-------|
| `head_sha` | `8120cc3148ab024ec5cddbe26beb0dc175daee7a` |
| `group_id` | _not captured — staging DB_ |
| `review_run_id` | _not captured — staging DB_ |
| `judge_status` | `completed` (inferred from publish + no withhold) |
| Transport `profile` seen | **`direct` only** — no gateway attempt; no `judge_llm_profile_fallback` |
| Billing | `revy-judge` key **US$0.37** Jul 26–31 (confirms billable inference vs T0 $0) |

## Baseline (T0 — `--since 2026-07-30T08:28:45Z`, post–#71 D0 deploy)

| Metric | Value |
|--------|-------|
| `candidate_runs.runs` | 49 |
| `candidate_runs.with_outcomes` | 28 |
| `candidate_runs.all_failed` | 21 |
| `candidate_runs.skipped_unavailable` | 17 |
| `manifest_candidates.with_parse_error` | 1 |
| Incident `review_run_id` | `019fb6d7-bb98-73e6-9743-1661630be275` |

## After deploy (T3 — post–#75 `2026-07-31T12:18:17Z`)

| Metric | T0 baseline | Post-deploy | Notes |
|--------|-------------|-------------|-------|
| `all_failed` | 21 | _PENDING T3.2_ | re-run metrics script |
| `skipped_unavailable` | 17 | _PENDING T3.2_ | re-run metrics script |
| Worker log: `judge_llm_request_completed` | absent | **present** | probe #76 `misc/log.txt` L63 |
| Smoke gateway + direct | partial (laptop) | **direct PASS** (probe E2E); gateway _PENDING_ | RTU down; gateway creds not observed on worker |

## Smoke matrix (T3.1)

| Path | Operator laptop (2026-07-31) | Staging (probe #76 E2E) |
|------|------------------------------|-------------------------|
| Gateway (RTU) | **FAIL** — RTU down | **NOT EXERCISED** — no gateway profile in worker log |
| Direct | **SKIP** — no local key | **PASS** — `api.anthropic.com` 200 ~3.7s; billing US$0.37 |

**Operator note:** RTU is down (expected). Gateway→direct **fallback** (`judge_llm_profile_fallback`) not proven on this run because worker appears **direct-only** (no `ANTHROPIC_BASE_URL`+token). To close JT-Q6 fallback gate: set dual credentials on droplet, re-run smoke or probe while RTU down — expect `judge_llm_profile_fallback` then direct success.

## Live run (T3.3)

| Field | Value |
|-------|-------|
| `head_sha` | `8120cc3148ab024ec5cddbe26beb0dc175daee7a` |
| `review_run_id` | _not captured_ |
| Log snippet | `misc/log.txt` — `judge_llm_request_started` 12:23:45 UTC → `POST api.anthropic.com/v1/messages` 200 12:23:48 → `judge_llm_request_completed` → `github_reconcile_complete` 12:23:49 → `github_publish_complete` 12:24:20 |
| `judge_status` | `completed` (inferred) |
| vs T0 incident | T0: ~5ms HTTP 200, $0 billing, `skipped_unavailable`. T3: ~3.7s inference, billable tokens, publish OK |

## Sign-off

- [x] T0 manifest root cause locked (JT-Q2)
- [x] T1+T2 unit tests green on branch
- [ ] T3.1 smoke PASS on staging droplet (gateway when RTU up + explicit `--compare-direct`)
- [ ] T3.2 metrics trend improved post-deploy
- [x] T3.3 probe PR live run + worker tail signed off (**direct path + T1 logging**)
- [ ] Program PASS: **PARTIAL** — direct transport verified; gateway fallback + JT-Q6 dual-cred gate open

**Ops note:** Optional `LOG_FORMAT=json` on worker droplet for richer `extra` fields without code changes.
