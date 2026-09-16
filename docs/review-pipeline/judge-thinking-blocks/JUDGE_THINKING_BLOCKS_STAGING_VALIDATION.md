# Judge thinking-blocks — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [JUDGE_THINKING_BLOCKS_FINDINGS.md](./JUDGE_THINKING_BLOCKS_FINDINGS.md)

**Status:** S1 **PASS** on [#106](https://github.com/raimondskrauklis/revy/pull/106) `b51c4c8` — discovery judge RTU opus-5 (`POST /v1/messages` 200 × 2, 2 outcomes). Reviewer+publish kimi still **PASS**. Probe stays on `chore/jtb-rtu-staging-dogfood` until S3.

---

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| Baseline (pre-extract) | `2026-08-07T00:00:00Z` | Historical persistence only — **not** this sign-off |
| **#103 RTU + thinking-blocks** | `2026-09-16T14:01:00Z` | Image on staging — [Actions 35104976266](https://github.com/raimondskrauklis/revy/actions/runs/35104976266) |
| **RTU virtual key + worker recreate** | `2026-09-16T14:26:13Z` | **Push 2** — first completed run after 401 |

**Rule:** Use deploy job completion time, not merge time. See [staging-validation README](../staging-validation/README.md). Pre-deploy #103 reviews are excluded.

---

## Dogfood PR

| PR | Branch | Status |
|----|--------|--------|
| [#106](https://github.com/raimondskrauklis/revy/pull/106) | `chore/jtb-rtu-staging-dogfood` | **open** — S1 `b51c4c8` judge **completed** |

---

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Autostart after #103 deploy; confirm `rtu` model identity + completed review | **done** — review **failed** 401 (`81d8606`) |
| 2 | Re-run after `RTU_API_KEY` = RTU virtual key (`RTU_AUTH_TOKEN`) | **done** — review + publish **200** (`f6f8a34`) |
| 3 | S1 — `jtb_rtu_judge_probe` command injection (live `shell=True` call) | **done** — judge **completed** (`b51c4c8`) |

---

## Judge trigger (code — not guess)

`is_judge_candidate` in `backend/app/services/github_finding_judge.py`:

| Finding | Judge? |
|---------|--------|
| `error` or `critical` (any category) | **yes** |
| `security` and severity ≥ `warning` | **yes** |
| `warning`/`info` + bug/maintainability/other | **no** |
| Autostart PR profile | **standard** only (`enqueue_review_run` in `index_tasks.py`) — deep/critical `azure_ai/claude-fable-5-1` is **not** this dogfood path |

Reconcile then runs discovery judge (`record_review_run_judge_status_with_model`) and verification judge (`verify_still_open_escalation_groups`) on still-open escalation groups.

---

## Scenarios

| ID | What | Models | Status |
|----|------|--------|--------|
| S0 | Clean probe, 0 findings | embed voyage-4; reviewer+publish rtu kimi; judge skip | **PASS** push 2 |
| S1 | Command injection in `jtb_rtu_judge_probe.py` | + discovery judge rtu opus-5 `/v1/messages` | **PASS** push 3 |
| S2 | Leave defect (no hunk fix) | verification judge on still-open group | not started |
| S3 | Remove invocation / fix | closure without cutting judge | not started |
| S4 | Deep/critical profile | reviewer `azure_ai/claude-fable-5-1` | not started — needs Deep/Critical from app, not autostart |

---

## Pass criteria — push 1 / #103 window (`2026-09-16T14:01:00Z`)

Expected live path: reviewer/publish `rtu` + `azure_ai/kimi-k2.7-code`; judge `rtu` + `azure_ai/claude-opus-5` when escalated.

| Check | Status | Evidence |
|-------|--------|----------|
| Index embed identity | **PASS** | MRC `--pr-number 106`: `index_embed` `voyage` / `voyage-code-4`; `parity_pass=1` |
| Reviewer provider + model | **PASS** | MRC `model_breakdown`: `review` `rtu` / `azure_ai/kimi-k2.7-code` `n=1`; origin `https://llm.ai.rtu.lv/v1/chat/completions` |
| Review HTTP | **FAIL** | Check run `81d8606` 10s: `401 Unauthorized` on that URL; PO `failed_runs=1` `failure_class=provider_error` |
| Completed review run | **FAIL** | PO `completed_runs=0` in the 401 window |
| Judge `rtu` / opus-5 | **INCONCLUSIVE** | Review never completed |
| Publish `rtu` / kimi | **INCONCLUSIVE** | `publish_summary.completed_jobs=0` |
| Candidate → `outcome` (thinking-blocks) | **INCONCLUSIVE** | `total_candidates=0` |

---

## Pass criteria — push 2 / key-fix window (`2026-09-16T14:26:13Z`)

| Check | Status | Evidence |
|-------|--------|----------|
| Index embed | **PASS** | MRC: `voyage` / `voyage-code-4`; snapshot `dimensions=1024`; Voyage HTTP 200 in worker log |
| Reviewer `rtu` + kimi | **PASS** | Snapshot `reviewer={provider:rtu, model_id:azure_ai/kimi-k2.7-code}`; `POST …/v1/chat/completions` 200; PO `completed_runs=1` `failed_runs=0` |
| Publish `rtu` + kimi | **PASS** | Snapshot `publish` same ids; second `POST …/v1/chat/completions` 200; issue comment [5699139935](https://github.com/raimondskrauklis/revy/pull/106#issuecomment-5699139935); `github_publish_complete` |
| Revy check | **PASS** | `pass` 50s, `2026-09-16T14:26:54Z`–`14:27:44Z`, head `f6f8a34` |
| Judge `rtu` + opus-5 | **skipped** | `judge_status=not_applicable`; `judge_escalation_candidate_count=0`; snapshot `judge=null`; no `/v1/messages` in worker log. MRC `judge` step `with_model_fields=0/1` |
| Candidate → `outcome` | **INCONCLUSIVE** | Judge metrics `--since 2026-09-16T14:26:13Z`: `total_candidates=0` (clean probe, no error/critical) |

---

## Metrics

```bash
cd backend
SINCE=2026-09-16T14:26:13Z   # push 2 (after key fix)
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
| Cause | `RTU_API_KEY` was LiteLLM `PROXY_MASTER_KEY`; origin expects virtual key `RTU_AUTH_TOKEN` |

### Push 2 — after virtual key (`f6f8a34`, 2026-09-16)

| Field | Value |
|-------|-------|
| `head_sha` | `f6f8a34` |
| `review_run_id` | `01a0aa9d-1f9a-731b-bcac-ea5333e46799` |
| `pipeline_run_id` | `01a0aa9d-0a43-7a14-aa2e-2d52f9051bbd` |
| Revy check | **pass** |
| Comment | [revybot on #106](https://github.com/raimondskrauklis/revy/pull/106#issuecomment-5699139935) — 0 findings, revision 2 |

`models_snapshot`:

```json
{
  "embedding": {"provider": "voyage", "model_id": "voyage-code-4", "dimensions": 1024},
  "reviewer": {"provider": "rtu", "model_id": "azure_ai/kimi-k2.7-code"},
  "judge": null,
  "publish": {"provider": "rtu", "model_id": "azure_ai/kimi-k2.7-code"}
}
```

### Push 3 — S1 judge probe (`b51c4c8`, 2026-09-16)

| Field | Value |
|-------|-------|
| Branch | `chore/jtb-rtu-staging-dogfood` ([#106](https://github.com/raimondskrauklis/revy/pull/106)) — **not** #105 |
| `head_sha` | `b51c4c8` |
| Reviewer | `POST …/v1/chat/completions` 200 |
| Judge | `judge_llm_request_started` × 2; `POST …/v1/messages` 200 × 2 |
| Outcomes | both `discovery` / `modified`; `rtu` / `azure_ai/claude-opus-5`; `warning`+`security` (eligible: security ≥ warning) |
| Publish | chat 200; two inline comments on probe + test |

Do **not** “fix” `shell=True` until S3 — those Revy threads are the S1 fixture.

`models_snapshot`:

```json
{
  "embedding": {"provider": "voyage", "model_id": "voyage-code-4", "dimensions": 1024},
  "reviewer": {"provider": "rtu", "model_id": "azure_ai/kimi-k2.7-code"},
  "judge": {"provider": "rtu", "model_id": "azure_ai/claude-opus-5"},
  "publish": {"provider": "rtu", "model_id": "azure_ai/kimi-k2.7-code"}
}
```

### Historical baseline (pre-#103 worker — not this pass)

| Metric | Baseline (2026-08-21) | `--since 2026-08-07T00:00:00Z` (2026-09-16) |
|--------|----------------------|-----------------------------------------------|
| Outcome persistence | **62.4%** (88/141) | **62.7%** (128/204) |
| `parse_error` | 53 × `Anthropic response invalid` | 76 × `Anthropic response invalid` (still pre-extract codes) |
| text-later vs thinking-only | 45 / 8 | **64 / 12** (`thinking_split`) |
| `retry_count` > 0 | 0 | **0** (JTB-Q5 still 0) |
| D9 ceiling noted | 94.3% | 94.3% |

---

## Root cause (push 1, closed)

| Hypothesis | Likelihood | Notes |
|------------|------------|-------|
| Staging `RTU_API_KEY` was proxy master key, not RTU virtual key | **confirmed** | Push 2 200 after switching to `RTU_AUTH_TOKEN` from `~/rtu-proxy/.env` |
| Product routing bug | **ruled out** | Push 1 already posted `llm.ai.rtu.lv` + `azure_ai/kimi-k2.7-code` |

---

## Next

| ID | Option | Verdict |
|----|--------|---------|
| A | Virtual key on origin | **done** — push 2 |
| D | S1 command-injection probe so discovery judge hits `POST /v1/messages` | **done** — 2× 200, 2 outcomes `modified` |
| E | S2 verification judge (leave probe), then S3 remove it | **next** |
| F | S4 deep/critical fable-5-1 via app review button | after S2; autostart cannot hit it |

---

## Sign-off

| Check | Status | Evidence |
|-------|--------|----------|
| RTU reviewer + publish live path | **PASS** | Push 2 snapshot + worker 200s + Revy pass on `f6f8a34` |
| RTU judge opus-5 HTTP | **PASS** | Push 3: `POST …/v1/messages` 200 × 2; snapshot `judge={rtu, azure_ai/claude-opus-5}`; `judge_status=completed`; 2 discovery outcomes |
| Staging PASS (≥95% **or** classified residual) | **INCONCLUSIVE** | No post-deploy judge candidates; D9 ceiling still noted |
| Do not reopen JSON-contract for 0.7pt | locked (D7/D9) | findings |
