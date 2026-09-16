# Judge thinking-blocks — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [JUDGE_THINKING_BLOCKS_FINDINGS.md](./JUDGE_THINKING_BLOCKS_FINDINGS.md)

**Status:** **FAIL** — post-#103 worker routes reviewer to RTU, but chat completions returns HTTP 401. Judge/publish not reached. Thinking-block extract cannot be signed off until a completed review run exists after the deploy boundary.

---

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| Baseline (pre-extract) | `2026-08-07T00:00:00Z` | Historical persistence only — **not** this sign-off |
| **#103 RTU + thinking-blocks** | `2026-09-16T14:01:00Z` | **This pass** — [Actions 35104976266](https://github.com/raimondskrauklis/revy/actions/runs/35104976266) deploy job completed |

**Rule:** Use deploy job completion time, not merge time. See [staging-validation README](../staging-validation/README.md). Pre-deploy #103 reviews are excluded.

---

## Dogfood PR

| PR | Branch | Status |
|----|--------|--------|
| [#106](https://github.com/raimondskrauklis/revy/pull/106) | `chore/jtb-rtu-staging-dogfood` | **open** — push 1 probe `post-main-dogfood-v8-rtu-provider` (`81d8606`) |

---

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Autostart after #103 deploy; confirm `rtu` model identity + completed review | **done** — review **failed** 401 |

---

## Pass criteria — push 1 / #103 window (`2026-09-16T14:01:00Z`)

Expected live path: reviewer/publish `rtu` + `azure_ai/kimi-k2.7-code`; judge `rtu` + `azure_ai/claude-opus-5` when escalated.

| Check | Status | Evidence |
|-------|--------|----------|
| Index embed identity | **PASS** | MRC `--pr-number 106`: `index_embed` `voyage` / `voyage-code-4`; `parity_pass=1` |
| Reviewer provider + model | **PASS** | MRC `model_breakdown`: `review` `rtu` / `azure_ai/kimi-k2.7-code` `n=1`; origin `https://llm.ai.rtu.lv/v1/chat/completions` |
| Review HTTP | **FAIL** | Check run `81d8606` 10s: `401 Unauthorized` on that URL; PO `failed_runs=1` `failure_class=provider_error` `wait_ms_p50=170` |
| Completed review run | **FAIL** | PO `completed_runs=0` |
| Judge `rtu` / opus-5 | **INCONCLUSIVE** | No judge step — review never completed |
| Publish `rtu` / kimi | **INCONCLUSIVE** | `publish_summary.completed_jobs=0` |
| Candidate → `outcome` (thinking-blocks) | **INCONCLUSIVE** | Judge metrics `--since 2026-09-16T14:01:00Z`: `total_candidates=0` |

---

## Metrics

```bash
cd backend
SINCE=2026-09-16T14:01:00Z
PR=106

DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  "python -m scripts.model_run_capture_staging_metrics --since $SINCE --pr-number $PR --json"

DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  "python -m scripts.pipeline_observability_staging_metrics --since $SINCE --pr-number $PR --json"

DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  "python -m scripts.judge_json_contract_staging_metrics --since $SINCE --json"
```

Historical extract window (pre-deploy; do not use for this sign-off):

```bash
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since 2026-08-07T00:00:00Z --json'
```

---

## Results (operator)

### Push 1 — post-#103 (`81d8606`, 2026-09-16)

| Field | Value |
|-------|-------|
| `head_sha` | `81d8606` |
| Revy check | **fail** `2026-09-16T14:06:27Z`–`14:06:37Z` |
| Summary | `Client error '401 Unauthorized' for url 'https://llm.ai.rtu.lv/v1/chat/completions'` |

### Historical baseline (pre-#103 worker — not this pass)

| Metric | Baseline (2026-08-21) | `--since 2026-08-07T00:00:00Z` (2026-09-16) |
|--------|----------------------|-----------------------------------------------|
| Outcome persistence | **62.4%** (88/141) | **62.7%** (128/204) |
| `parse_error` | 53 × `Anthropic response invalid` | 76 × `Anthropic response invalid` (still pre-extract codes) |
| text-later vs thinking-only | 45 / 8 | **64 / 12** (`thinking_split`) |
| `retry_count` > 0 | 0 | **0** (JTB-Q5 still 0) |
| D9 ceiling noted | 94.3% | 94.3% |

---

## Root cause

| Hypothesis | Likelihood | Notes |
|------------|------------|-------|
| `RTU_API_KEY` rejected by LiteLLM (wrong/expired/not the virtual key) | **high** | Empty key would raise `llm_disabled` before HTTP; 401 means a Bearer token was sent |
| Worker env not the key operators intended after restart | medium | Confirm `RTU_API_KEY` on api+workers; do not set `ANTHROPIC_BASE_URL` for RTU |
| Product routing bug (Moonshot URL / provider) | **low** | Breakdown is `rtu` + `azure_ai/kimi-k2.7-code` against `llm.ai.rtu.lv` |

---

## Next

| ID | Option | Verdict |
|----|--------|---------|
| A | Set a valid `RTU_API_KEY` on the droplet; recreate api+workers (no OS reboot) | **do this** |
| B | After A, empty-commit re-trigger on [#106](https://github.com/raimondskrauklis/revy/pull/106) and re-run the three scripts | after A |
| C | Change request auth in product code | **no** until A is verified — routing already matches the live path |

---

## Sign-off

| Check | Status | Evidence |
|-------|--------|----------|
| RTU reviewer/judge live path | **FAIL** | 401 on RTU chat completions; judge never ran |
| Staging PASS (≥95% **or** classified residual) | **INCONCLUSIVE** | No post-deploy judge candidates |
| Do not reopen JSON-contract for 0.7pt | locked (D7/D9) | findings |

**Next:** operator A → re-trigger #106 → fill push 2.
