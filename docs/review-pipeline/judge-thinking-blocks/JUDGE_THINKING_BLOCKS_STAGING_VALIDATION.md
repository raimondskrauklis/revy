# Judge thinking-blocks — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [JUDGE_THINKING_BLOCKS_FINDINGS.md](./JUDGE_THINKING_BLOCKS_FINDINGS.md)

**Status:** S0–S2 **PASS**. S3 **PASS** on [#106](https://github.com/raimondskrauklis/revy/pull/106) `fb28cd3` — probe/test files deleted; both security groups `resolved`/`addressed`/`absent_and_addressed`. Hunk-only S3 stayed **PARTIAL** (verification **upheld**). S4 blocked — no Deep/Critical in `/reviewer`; admin `POST …/review` needs Keycloak.

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
| [#106](https://github.com/raimondskrauklis/revy/pull/106) | `chore/jtb-rtu-staging-dogfood` | **open** — S3 **PASS** at `fb28cd3`; S4 not started |

---

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Autostart after #103 deploy; confirm `rtu` model identity + completed review | **done** — review **failed** 401 (`81d8606`) |
| 2 | Re-run after `RTU_API_KEY` = RTU virtual key (`RTU_AUTH_TOKEN`) | **done** — review + publish **200** (`f6f8a34`) |
| 3 | S1 — `jtb_rtu_judge_probe` command injection (live `shell=True` call) | **done** — judge **completed** (`b51c4c8`) |
| 4 | S2 — docs-only, leave probe hunks | **done** — verification `upheld` (`9843a7e`) |
| 5 | S3 — remove `shell=True` | **done** — display-clean, DB verification **upheld** (`a538d4d`) |
| 6 | S3 follow-up — drop stale README instruction | **done** — Revy **pass**, 0 open tables (`a761f74`) |
| 7 | Record push 6 evidence | **done** (`0c69a56`) |
| 8 | S3b — delete probe + test files | **done** — both groups `addressed`/`absent_and_addressed` (`fb28cd3`) |

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
| S2 | Leave defect (no hunk fix) | verification judge on still-open group | **PASS** push 4 |
| S3 | Remove invocation / fix | closure without cutting judge | **PASS** push 8 (file delete); hunk-only was **PARTIAL** |
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

### Push 4 — S2 leave probe (`9843a7e`, 2026-09-16)

| Field | Value |
|-------|-------|
| `head_sha` | `9843a7e` (docs only — probe hunks untouched) |
| `review_run_id` | `01a0aab1-63bc-7f12-a554-7df921aee6a7` |
| Discovery | 1 candidate — new title on probe module (`modified`) |
| Verification | unit-test group `upheld`; `resolution_status=still_open`; `state=active` |
| Judge | snapshot `rtu` / `azure_ai/claude-opus-5`; `judge_status=completed` |

### Push 5 — S3 remove injection (`a538d4d`, 2026-09-16)

| Field | Value |
|-------|-------|
| `head_sha` | `a538d4d` |
| This generation | `info`/`maintainability` on program README only (not judge-eligible) |
| Discovery judge | `not_applicable`, 0 candidates |
| Verification | 2× `upheld` (probe + test groups remain `active`/`still_open`) |
| GitHub tables | security rows hidden; 1 INFO still open |
| Snapshot | reviewer+publish `rtu` kimi; `judge=null` (no discovery candidates) |

S3 did **not** get `addressed`/`resolved` on the security groups — verification judged the still-open claims as still valid after the hunk edit. Display hygiene still improved.

### Push 6 — S3 follow-up (`a761f74`, 2026-09-16)

| Field | Value |
|-------|-------|
| `head_sha` | `a761f74` |
| Revy check | **pass** `2026-09-16T14:58:56Z`–`15:00:28Z` (1m32s) |
| This generation | 0 publishable findings |
| INFO README group | `resolved` / `addressed` |
| Verification | 2× `upheld` opus-5 (same two security groups still `active`/`still_open`) |
| GitHub | Ready to merge; raised 3, resolved 1, display open 0, hidden 2 (collapsed threads) |
| Snapshot | reviewer+publish `rtu` kimi; `judge=null` (no discovery candidates); verification still ran |

Push-delta for the probe files was empty on this docs-only revision, so verification re-judged the prior titles against no hunk and **upheld** again. That is why DB `still_open` outlives GitHub display-clean.

### Push 8 — S3b delete probe files (`fb28cd3`, 2026-09-16)

| Field | Value |
|-------|-------|
| `head_sha` | `fb28cd3` |
| Revy check | **pass** `2026-09-16T15:13:03Z`–`15:14:49Z` (1m46s) |
| Probe group | `resolved` / `addressed` / `absent_and_addressed` |
| Test group | `resolved` / `addressed` / `absent_and_addressed` |
| This generation | 1 discovery candidate on the validation memo (`critical`/`security`, title said fixture not yet deleted) — judge **dismissed** |
| Snapshot | reviewer+publish `rtu` kimi; judge `rtu` / `azure_ai/claude-opus-5` |
| GitHub | raised 4, resolved 4, display open 0 (path removed 2, judge dismissed 1, addressed 1) |

Hunk-only S3 did **not** close DB groups. File delete did, via `file_path_deleted_in_compare`. The superseded original injection title remains `still_open` on a non-active group.

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
| E | S2 verification judge (leave probe), then S3 remove it | S2 **PASS**; hunk S3 **PARTIAL**; file-delete S3b **PASS** |
| F | S4 deep/critical fable-5-1 via app review button | **blocked** — `/reviewer` has no Deep/Critical control; admin `POST …/review` needs Keycloak SSO |

---

## Sign-off

| Check | Status | Evidence |
|-------|--------|----------|
| RTU reviewer + publish live path | **PASS** | Push 2 snapshot + worker 200s + Revy pass on `f6f8a34` |
| RTU judge opus-5 HTTP | **PASS** | Push 3: `POST …/v1/messages` 200 × 2; snapshot `judge={rtu, azure_ai/claude-opus-5}`; `judge_status=completed`; 2 discovery outcomes |
| Staging PASS (≥95% **or** classified residual) | **INCONCLUSIVE** | No post-deploy judge candidates; D9 ceiling still noted |
| Do not reopen JSON-contract for 0.7pt | locked (D7/D9) | findings |
