# Judge transport reliability — staging validation

**Date:** T0 baseline 2026-07-31; T3 operator gate open 2026-07-31 (post–#75 deploy)  
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
| `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` on worker | RTU gateway URL + token | _PENDING deploy verify_ |
| `ANTHROPIC_API_KEY` on worker | Direct Anthropic fallback | _PENDING deploy verify_ |
| `judge_llm_enabled()` | `true` when gateway **or** direct configured | _PENDING droplet verify_ |

## T3 probe PR (live judge + transport)

**Branch:** `chore/judge-transport-staging-probe` · **Fixture:** `backend/app/services/jt_transport_staging_probe.py`

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce judge-eligible probe (`critical`/`security` shell injection) | pending |

**Pass criteria (push 1):**

| Check | Pass | Evidence |
|-------|------|----------|
| ≥1 publishable finding on probe file | pending | Revy issue comment / `summary_json` |
| `judge_escalation_candidate_count` ≥ 1 | pending | staging DB or publish summary |
| Worker: `judge_llm_request_started` + `judge_llm_request_completed` | pending | droplet tail (redacted) |
| `judge_status` = `completed` (not `skipped_unavailable`) | pending | `review_run` row |
| Outcome row persisted | pending | `github_finding_judge_outcomes` |

### Operator protocol — parallel flow + behavior

Run **both** tracks when the probe PR review starts on staging:

| Track | What | Command / action |
|-------|------|------------------|
| **A — E2E flow** | Full pipeline: Moonshot → reconcile → discovery judge | Open probe PR; trigger staging Revy review; record `head_sha`, `review_run_id` |
| **B — Transport behavior** | Real gateway/direct paths (not mocked) | On droplet with staging `.env`: `cd backend && pipenv run python -m scripts.test_anthropic_judge_gateway --compare-direct --print-raw` |
| **C — Metrics** | Post-deploy trend vs T0 | `cd backend && DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics --since 2026-07-31T12:18:17Z --json` |

**Worker tail (paste into Live run §):**

```bash
# replace container name if needed
docker logs -f --since 5m revy-worker 2>&1 | grep -E 'judge_llm_request_|judge_llm_profile_fallback|github_finding_judge_failed'
```

**What to look for (real errors, not just happy path):**

| Log event | Meaning |
|-----------|---------|
| `judge_llm_request_started` | Transport logging live (`profile`, `messages_url`, `model_id`) |
| `judge_llm_profile_fallback` | Gateway failed → direct attempt (RTU down, HTTP error, empty/invalid body) |
| `judge_llm_request_completed` | Successful inference (`duration_ms`, `response_chars`, usage fields) |
| `github_finding_judge_failed` | Judge failed — check `error`, `parse_error`, `response_body_preview` in `extra` (use `LOG_FORMAT=json` if plain text hides fields) |

**Cohort row (fill after push 1 PASS):**

| Field | Value |
|-------|-------|
| `head_sha` | _PENDING_ |
| `group_id` | _PENDING_ |
| `review_run_id` | _PENDING_ |
| `judge_status` | _PENDING_ |
| Transport `profile` seen | _PENDING_ (`gateway` / `direct` / fallback both) |

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
| Worker log: `judge_llm_request_completed` | absent | _PENDING T3.3_ | probe PR + droplet tail |
| Smoke gateway + direct | partial (laptop) | _PENDING T3.1_ | droplet smoke script |

## Smoke matrix (T3.1)

| Path | Operator laptop (2026-07-31) | Staging droplet |
|------|------------------------------|-----------------|
| Gateway (RTU) | **FAIL** — RTU down | _PENDING_ |
| Direct | **SKIP** — no local key | _PENDING_ |

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
- [ ] T3.1 smoke PASS on staging droplet (gateway when RTU up + direct)
- [ ] T3.2 metrics trend improved post-deploy
- [ ] T3.3 probe PR live run + worker tail signed off
- [ ] Program PASS: **IN PROGRESS** — post–#75 deploy done; operator gate open

**Ops note:** Optional `LOG_FORMAT=json` on worker droplet for richer `extra` fields without code changes.
