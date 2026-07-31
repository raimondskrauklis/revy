# Judge LLM transport reliability — findings

**Date:** 2026-07-31  
**Purpose:** Baseline for a **general plan** — judge LLM path must work reliably across RTU gateway and direct Anthropic (and future providers) with **one judging workflow** and **operator-visible failures**. No execution steps.

**Trigger:** Staging worker logs (PR #72, sha `77300ab`, 2026-07-31 ~06:26 UTC) show discovery judge failure after `api.anthropic.com` HTTP 200 with **no Anthropic billing**; RTU (`https://llm.ai.rtu.lv/`) reported down. FR-CS4 Pass 3 dogfood exposed a **separate** reconcile/supersede product gap — do not conflate with transport.

**Authority:** [JUDGE_JSON_CONTRACT_FINDINGS.md](../judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md) (parse/observability wave, 2026-07-28) · [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](./JUDGE_INPUT_INVESTIGATION_FINDINGS.md) · operator logs `misc/workerlogs.txt` · [BACKEND_SCRIPTS_RUNBOOK.md](../../utils/BACKEND_SCRIPTS_RUNBOOK.md)

---

## Build principles

1. **One judge workflow** — candidates → prompts → `call_judge_with_optional_retry` → outcome → closure/publish. Transport (RTU vs direct vs Bedrock) is an adapter; must not fork product logic.
2. **Fail loud, fail traceable** — Celery/worker logs must show *which profile*, *what error*, and enough response context to debug without DB shell access.
3. **No silent withhold** — RG-6 (withhold publish without outcome) is correct; operators need to know *why* (`judge_candidate_unpublished_missing_outcome` is not enough alone).
4. **Gateway-first, direct fallback** — locked additive design (`anthropic_review.py`); fallback must cover real production failure modes (down gateway **and** bad gateway responses).
5. **Do not confuse tracks** — transport reliability ≠ Pass 3 eligibility / supersede timing (finding-resolution FR-CS4).

---

## Terminology

| Term | Meaning |
|------|---------|
| **Discovery judge** | Pre-publish escalation — `record_review_run_judge_status` · `JUDGE_SYSTEM_PROMPT` |
| **Verification judge (Pass 3)** | Post-reconcile `still_open` — `verify_still_open_escalation_groups` · `VERIFICATION_JUDGE_SYSTEM_PROMPT` |
| **Gateway profile** | RTU LiteLLM — `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` → `{base}/v1/messages` |
| **Direct profile** | Native Anthropic — `ANTHROPIC_API_KEY` → `api.anthropic.com/v1/messages` |
| **Profile fallback** | `_post_judge_with_profile_fallback` — gateway profile may fall through to direct on HTTP, empty/invalid body, or parse error |

---

## Summary

**Verified:** Judge uses a **single workflow** for discovery and Pass 3; RTU and direct are **two HTTP profiles inside** `anthropic_review.judge_finding()`, not parallel judge products.

**Verified:** When RTU is unreachable, code **should** fall back to direct Anthropic if `ANTHROPIC_API_KEY` is set (`anthropic_review.py:296–336`).

**Verified (operator incident):** One reconcile run hit **direct** Anthropic (`api.anthropic.com` 200), then `github_finding_judge_failed` **~5ms** later, then `judge_candidate_unpublished_missing_outcome`. That latency pattern is **not** a full model inference; billing showing **zero tokens** is consistent with empty/invalid response or request never reaching billable inference.

**Unknown (RTU down):** No completed HTTP log line to `llm.ai.rtu.lv` in captured worker tail; cannot confirm gateway attempt vs staging env omitting gateway vars. P0 smoke (2026-07-29) showed RTU plain JSON **pass** at ~3.6s when gateway was up.

**Verified (T1+T2):** Worker logs emit `judge_llm_request_started/completed` and `judge_llm_profile_fallback`; failure extras include transport fields. Gateway empty-body, parse-error, and non-JSON 200 responses fall through to direct when configured.

**Gap (pre-staging deploy):** Console formatter may still hide structured `extra` without `LOG_FORMAT=json` — optional ops toggle.

---

## Architecture (verified)

```text
[Judge workflow — unified]
  reconcile_tasks
    → record_review_run_judge_status (discovery)
    → verify_still_open_escalation_groups (Pass 3)
  github_finding_judge.call_judge_with_optional_retry
    → llm_dispatch.call_judge_llm
    → anthropic_review.judge_finding | bedrock_review.judge_finding
  parse_judge_outcome → DB outcome → closure / publish gate

[Anthropic transport — two profiles, one adapter]
  _judge_profiles: [gateway?, direct?]
  _post_judge_with_profile_fallback: HTTP / empty body / parse → direct (gateway only)
```

| Layer | File | Role |
|-------|------|------|
| Pipeline | `backend/app/workers/reconcile_tasks.py:47–73` | Order: reconcile → Pass 2 → discovery judge → Pass 3 |
| Workflow | `backend/app/services/github_finding_judge.py` | Candidates, prompts, retry, outcomes, `judge_status` |
| Pass 3 | `backend/app/services/github_finding_closure.py:268+` | Reuses `call_judge_with_optional_retry` |
| Dispatch | `backend/app/integrations/llm_dispatch.py:47–80` | `anthropic` \| `bedrock` |
| Transport | `backend/app/integrations/anthropic_review.py:88–336` | Gateway + direct profiles, structured-output policy |
| Publish gate | `backend/app/services/github_publish.py:984–993` | `judge_candidate_unpublished_missing_outcome` |
| Manifest | `backend/app/services/github_pipeline_trace.py:538–595` | `parse_error`, `raw_response_text` on failures |
| Config | `backend/app/core/config.py:217–292` | `anthropic_gateway_enabled`, `judge_llm_enabled()` |

---

## What exists (post JSON-contract / gateway work)

| Area | State | Evidence |
|------|-------|----------|
| Gateway-first profiles | **Shipped** | `anthropic_review.py:102–111`, `:296–336` |
| Direct fallback on HTTP error | **Shipped** | `judge_llm_profile_fallback` warning |
| Parse retry (once) | **Shipped** | `call_judge_with_optional_retry` — `JudgeParseError`, `judge_outcome_invalid` only |
| Failure body in manifest | **Shipped** | `JudgeCandidateArtifact.raw_response_text`, `parse_error` |
| Structured output on gateway | **Off (locked)** | `JUDGE_GATEWAY_STRUCTURED_OUTPUT_SUPPORTED = False`; P0 RTU 400 on structured |
| Structured output on direct | **Optional** | `REVY_JUDGE_STRUCTURED_OUTPUT` (default false) |
| Smoke script | **Shipped** | `scripts/test_anthropic_judge_gateway.py` (`--compare-direct`, `--print-raw`) |
| Staging metrics | **Shipped** | `scripts/judge_json_contract_staging_metrics.py` |
| Worker profile/usage logging | **Shipped (T1)** | `judge_llm_request_started/completed`, transport fields on failure |
| Fallback on gateway parse / empty / non-JSON body | **Shipped (T2)** | Gateway profile → direct via `allow_judge_profile_fallback` |
| Celery-visible error detail | **Improved (T1)** | Named log events; optional `LOG_FORMAT=json` for full `extra` |

---

## Operator incident (verified from `misc/workerlogs.txt`)

**Context:** PR #72 doc push `77300aba…`, reconcile ~2026-07-31 06:25:54–06:26:07 UTC.

| Step | Log | Interpretation |
|------|-----|----------------|
| Review | Moonshot `200` ~06:25:54 | Reviewer OK |
| Reconcile start | `reconcile_review_run` 06:25:54 | — |
| Compare + context | GitHub fetches 06:25:55–57 | Engineering context for judge |
| Judge HTTP | `POST api.anthropic.com/v1/messages` **200** 06:26:06.777 | **Direct** profile (no `llm.ai.rtu.lv` line) |
| Judge fail | `github_finding_judge_failed` 06:26:06.782 | **~5ms** after HTTP — local reject, not multi-second inference |
| Reconcile end | `github_reconcile_complete` 06:26:07 | — |
| Publish | `judge_candidate_unpublished_missing_outcome` 06:26:07 | RG-6 withhold |
| Pass 3 compare | Second GitHub compare 06:26:07 | Verification path ran; no Anthropic line → likely 0 candidates |

**Not in tail:** `anthropic_profile_failed_trying_fallback` (may be filtered or gateway not configured).

**Operator report:** Anthropic billing dashboard shows **no tokens** for that window — consistent with non-inference or wrong billing account vs staging key.

**Root cause confirmed (T0 — staging manifest 2026-07-31):** `review_run_id` `019fb6d7-bb98-73e6-9743-1661630be275`, head `77300aba5b7ae6da1315c43ed349b706f95c55d9`. Judge manifest: `parse_error` = `Anthropic response invalid`, `raw_response_text` null, `retry_count` 0, `judge_status` = `skipped_unavailable`. Matches **direct** profile (`api.anthropic.com` 200 in worker tail): `_extract_message_text` rejected the body (empty/missing `content[].text`) — not a multi-second inference and no billable tokens. Gateway was not attempted in logs; dual-credential staging (JT-Q6) still required for RTU-down fallback on other runs. Validation memo: [JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md](./JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md).

---

## Gap catalog

| ID | Gap | Severity | Notes |
|----|-----|----------|-------|
| **JT-1** | Worker logs insufficient for transport debug | **high** | **addressed (T1)** — `judge_llm_request_started/completed`, transport fields on failure extras |
| **JT-2** | Gateway down visible only as absence of RTU URL | **medium** | **addressed (T1)** — `judge_llm_request_started` + `judge_llm_profile_fallback` with URL |
| **JT-3** | Fallback scope too narrow | **high** | **addressed (T2)** — gateway empty-body + parse → direct |
| **JT-4** | No `usage` / latency logged | **medium** | **addressed (T1)** — `duration_ms`, token usage on completion log |
| **JT-5** | RTU health unknown while down | **medium** | RTU down operator 2026-07-31; staging worker **direct-only** on probe #76 — gateway fallback not exercised; re-run when dual creds on droplet |
| **JT-6** | Same `model_ref` for both profiles | **low** | `resolve_model` returns `revy_anthropic_model`; gateway overrides model via `REVY_ANTHROPIC_GATEWAY_MODEL` inside profile — correct but opaque in logs |
| **JT-7** | `skipped_unavailable` aggregate hides per-candidate cause | **medium** | Metrics script counts runs; manifest has detail per candidate |
| **JT-8** | Pass 3 transport shares discovery failures | **medium** | Same adapter; fix benefits both — but Pass 3 also blocked by FR-CS4 supersede (separate) |

---

## Relationship to prior waves

| Program | Overlap |
|---------|---------|
| **Judge JSON contract (JC)** | Addressed parse helper, manifest `raw_response_text`, structured output policy. **Did not** address profile fallback on parse, worker logging, or RTU-down ops playbook. |
| **Judge input quality (P0–P5)** | Prompt/evidence quality. Orthogonal to transport unless prompt size triggers gateway timeouts. |
| **FR-CS4 / Pass 3 dogfood** | Proved Pass 3 **eligibility** failure (supersede before verify). Discovery judge **did** work on rev 7–8 when transport succeeded. |

---

## Edge cases

| Case | Current behavior | Risk |
|------|------------------|------|
| RTU connection refused | Fallback to direct if key set | OK if direct healthy |
| RTU only configured, no direct key | Judge fails entirely when RTU down | Staging outage = no judge |
| RTU returns 200, empty `content[].text` | Gateway: fallback to direct (T2); direct-only: `ServiceUnavailableError` | OK when dual credentials |
| RTU returns 200, invalid JSON | Gateway: fallback to direct (T2); direct-only: parse retry then fail | OK when dual credentials |
| RTU returns 200, non-JSON body | Gateway: `ServiceUnavailableError` → direct fallback (T2) | OK when dual credentials |
| Direct key wrong org vs billing UI | 401 typically; operator confusion | Ops |
| Parse fails twice | `skipped_unavailable` if any candidate missing outcome | Finding withheld |
| Pass 3 + discovery same run | Shared transport; separate prompts | Fix once in adapter |

---

## Advice / options (for general plan — not locked)

| Option | Action | Pros | Cons |
|--------|--------|------|------|
| **A — Transport observability** | Log `judge_llm_request` / `judge_llm_response` with `profile`, `url`, `model_id`, `duration_ms`, `usage`, `parse_error` snippet | Fixes JT-1, JT-2, JT-4; worker-debuggable | Log volume; redact prompts |
| **B — Widen profile fallback** | On `JudgeParseError` or empty body from `gateway` profile, try `direct` | Fixes JT-3; RTU “up but broken” | Double cost on failure; need cap |
| **C — Staging LOG_FORMAT=json** | Droplet env for worker | Full `extra` without code change | Ops change; log aggregation |
| **D — RTU recovery gate** | Re-run `test_anthropic_judge_gateway --compare-direct` when RTU returns | Confirms JT-5 | Blocked until RTU up |
| **E — Require both credentials on staging** | RTU + direct key documented in deploy | Fallback always available | Two billing paths |

**Recommended direction for general plan:** **A + B** in one transport-hardening wave; **C** or manifest export as short-term ops; **D** as verification gate; keep FR-CS4 supersede fix in finding-resolution track.

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| **JT-Q1** | Is judge workflow forked per endpoint? | **locked** | **No** — one workflow; two Anthropic HTTP profiles |
| **JT-Q2** | Primary failure mode in 06:26 incident? | **locked** | **Direct** profile HTTP 200 with invalid/empty message body → `ServiceUnavailableError` (`Anthropic response invalid`); manifest `raw_response_text` null — **T0** |
| **JT-Q3** | Fallback on gateway parse failure? | **locked** | **Yes** — see [general plan](./JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md) T2 |
| **JT-Q4** | Log full prompt on failure? | **locked** | **No** — profile + metrics + `parse_error`; manifest keeps prompt — **T1** |
| **JT-Q5** | Enable structured output on direct only? | **locked** | **Defer** until post-T3 metrics — parking lot |
| **JT-Q6** | Staging must have direct key when RTU primary? | **locked** | **Yes** — dual credentials — **T0** |

---

## Parking lot

| Item | Notes |
|------|-------|
| FR-CS4 supersede-before-Pass-3 | Finding-resolution product fix — not transport |
| Bedrock judge path | Same workflow via `bedrock_review.judge_finding` — include in logging design |
| `llm.rdi.services` proxy | Cursor-only per JC-D2 — out of scope |
| Moonshot as judge provider | Not supported in `SUPPORTED_JUDGE_PROVIDERS` |

---

## Devil's advocate

| Risk | Mitigation |
|------|------------|
| Logging prompts leaks code | Log hashes/chars only; full body in manifest/DB |
| Fallback to direct masks RTU outages | Metric: `judge_profile_fallback_total{from="gateway"}` |
| “Fix logging” without fixing fallback | JT-3 still loses findings when RTU returns garbage |
| Conflate with FR-CS4 | Keep transport wave separate; link in README only |

---

## Experiment / verification

| Experiment | Pass |
|------------|------|
| `test_anthropic_judge_gateway --compare-direct --print-raw` with RTU up | Gateway pass; direct pass or skip if no key |
| Same script with RTU down / blocked | Gateway fail logged; direct pass |
| Staging review with judge candidate + `LOG_FORMAT=json` | Log lines include `profile`, `parse_error` or `outcome` |
| Pipeline manifest for failed run | `candidates[].parse_error` + `raw_response_text` populated |
| `judge_json_contract_staging_metrics` after fix | `all_failed` / `skipped_unavailable` trend down |
| Anthropic billing | Input tokens > 0 on successful discovery judge run |

**Repro SQL (manifest)** — PR #72 incident `77300ab` (fallback: nearest run with `judge_escalation_candidate_count > 0`):

```sql
-- Staging: PRODUCTION_DATABASE_URL via backend/.env
SELECT
  rev.head_sha,
  rr.id AS review_run_id,
  rr.judge_status,
  rr.judge_escalation_candidate_count,
  a.content_json -> 'candidates' AS candidates
FROM github_review_runs rr
JOIN github_pull_request_revisions rev ON rev.id = rr.revision_id
JOIN github_pull_requests pr ON pr.id = rev.pull_request_id
JOIN github_pipeline_runs p ON p.review_run_id = rr.id
JOIN github_pipeline_steps s ON s.pipeline_run_id = p.id AND s.step_type = 'judge'
JOIN github_pipeline_artifacts a ON a.step_id = s.id AND a.kind = 'manifest'
WHERE pr.number = 72
  AND rev.head_sha LIKE '77300aba%'
  AND rr.status = 'completed'
ORDER BY rr.created_at DESC
LIMIT 1;
```

Read `candidates[]` fields: `parse_error`, `raw_response_text`, `retry_count`, `length(user_prompt)` (in JSON).

---

## References

| Doc / artifact | Link |
|----------------|------|
| Gateway env | `backend/.env.example` (ANTHROPIC_BASE_URL, AUTH_TOKEN, API_KEY) |
| P0 RTU smoke | [JUDGE_JSON_CONTRACT_FINDINGS.md](../judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md) § P0 smoke results |
| Worker logs (incident) | `misc/workerlogs.txt` |
| FR-CS4 handoff (Pass 3 separate) | finding-resolution dogfood staging memo Wave D |
| Metrics script | `backend/scripts/judge_json_contract_staging_metrics.py` |
| Logging format | `backend/app/core/logging.py` (`ConsoleFormatter` vs `JsonFormatter`) |

**Next step:** merge [PR #75](https://github.com/raimondskrauklis/revy/pull/75) → staging deploy → complete [validation memo](./JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md) T3.3 sign-off.
