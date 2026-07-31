# docs/review-pipeline/judge/JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md

# Judge LLM transport reliability — general plan

**Baseline:** [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](./JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md) (2026-07-31)  
**Prerequisite:** Judge JSON contract + gateway profile shipped (`anthropic_review.py`, manifest failure fields).

**Thesis:** One judge workflow; RTU gateway and direct Anthropic are **transport profiles** in the same adapter. Staging failures are often **invisible in worker tails** and **under-fallbacked** (HTTP-only). Harden transport + logging without forking discovery vs Pass 3 logic.

**Gap IDs:** **JT-*** in findings; **T0–T3** = program phases below.

**Locked (from findings + this plan):**

| ID | Resolution |
|----|------------|
| JT-Q1 | One workflow; profiles are transport only |
| JT-Q3 | **Yes** — gateway `JudgeParseError` or empty/invalid body → try direct profile (when configured) |
| JT-Q4 | Worker logs: **profile, url, model_id, duration_ms, usage summary, parse_error** — not full prompt (manifest keeps prompt) |
| JT-Q5 | Structured output on direct (`REVY_JUDGE_STRUCTURED_OUTPUT`) — **defer** until T3 metrics show parse failures remain after T1+T2 |
| JT-Q6 | Staging/production judge path: **RTU gateway + direct API key** both configured for fallback |
| FR-CS4 supersede | **Out of scope** — finding-resolution track |

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` — gateway fail, direct pass, parse-fail fallback, empty-body fallback, logging fields; Bedrock judge path unchanged but logging hooks must not break it.
- **Single workflow:** Changes only in `anthropic_review.py` (and thin call-site log enrichment in `github_finding_judge.py` / `github_finding_closure.py`) — no duplicate judge loops.
- **Security:** Never log full prompts or raw response bodies in worker INFO; truncated `parse_error` + `response_chars` only.
- **i18n:** Backend-only — no new UI strings.
- **RG-6:** Publish withhold without outcome stays locked.

---

## T0 — Incident baseline & prerequisites

**Goal:** Lock open decisions, confirm 06:26 failure mode from DB manifest, and document dual-credential staging requirement.

**Scope — in:** Resolve JT-Q2 from pipeline judge manifest (`raw_response_text`, `parse_error`) for PR #72 `77300ab` run; staging env checklist (gateway URL + token + direct key); update deploy/env examples for dual path; record baseline `judge_json_contract_staging_metrics` snapshot.

**Scope — out:** Code changes; RTU smoke (blocked while RTU down).

**Deliverables:** Findings decisions JT-Q2/Q3/Q4/Q6 marked locked in findings doc; incident root-cause note (1 paragraph); staging env gate documented.

**Depends on:** None.

---

## T1 — Worker-visible transport logging

**Goal:** Operator can debug judge transport from **Celery worker tail** without DB — see profile, endpoint, latency, and failure reason.

**Scope — in:** Structured log events on judge HTTP round-trip (`judge_llm_request_started`, `judge_llm_request_completed`, `judge_llm_profile_fallback`); fields: `profile`, `messages_url`, `model_id`, `duration_ms`, `input_tokens`/`output_tokens` when present in response, `outcome` or `parse_error`; enrich `github_finding_judge_failed` / `verification_judge_failed` `extra` with same fields; log gateway connection failures at WARNING with URL (not only httpx absence).

**Scope — out:** `LOG_FORMAT=json` droplet change (ops optional); prompt content in logs; metrics backend / Sentry.

**Deliverables:** Console-visible judge transport lines on staging tail; unit tests for log extras on success, HTTP fail, parse fail.

**Depends on:** T0.

---

## T2 — Gateway profile fallback hardening

**Goal:** When RTU is down **or** returns garbage (empty 200, unparseable JSON), fall through to direct Anthropic when configured — same user prompt, same judge workflow.

**Scope — in:** Extend `_post_judge_with_profile_fallback` / judge message path: after gateway profile, on `httpx.HTTPError`, `ServiceUnavailableError` (empty body), or `JudgeParseError` from gateway — try next profile; at most one fallback per candidate per call (no retry storm); preserve existing parse retry in `call_judge_with_optional_retry` after a **successful** profile returns text.

**Scope — out:** Changing profile order; Moonshot/Bedrock fallback chains; structured output on gateway.

**Deliverables:** Fallback behavior covered by unit tests; `anthropic_profile_failed_trying_fallback` (or successor event) includes `failure_class` (`http` | `empty_body` | `parse`).

**Depends on:** T0. May ship in parallel with T1 if tests are independent.

---

## T3 — Staging verification & ops gate

**Goal:** Prove transport reliability on staging after T1+T2 — RTU when up, direct when RTU down or broken.

**Scope — in:** Run `test_anthropic_judge_gateway --compare-direct --print-raw` when RTU returns; trigger staging review with judge-eligible finding; verify worker logs show profile + outcome; `judge_json_contract_staging_metrics` before/after; short validation memo (`JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md`); optional ops note for `LOG_FORMAT=json` on worker.

**Scope — out:** FR-CS4 Pass 3 product fix; enabling `REVY_JUDGE_STRUCTURED_OUTPUT` unless T3 metrics still show parse failures.

**Deliverables:** Staging PASS sign-off (gateway path + forced direct fallback scenario); metrics trend documented; judge README index row.

**Depends on:** T1, T2; RTU reachable for full gate (direct-only fallback test can run while RTU down).

---

## Parking lot

| Item | Notes |
|------|-------|
| `REVY_JUDGE_STRUCTURED_OUTPUT` on direct | After T3 if parse rate still high |
| Prometheus counters for `judge_profile_fallback` | Nice-to-have post-T1 |
| Manifest → CLI export for failed runs | Ops tooling |
| FR-CS4 supersede-before-Pass-3 | Finding-resolution — not this program |

---

## Devil's advocate

| Risk | Mitigation |
|------|------------|
| Logging fixes mask missing fallback | Ship T1 + T2 same release or T2 first |
| Double billing on gateway parse → direct | Accept for rare failure; log both attempts |
| RTU stays down — gate incomplete | T3 still passes on direct-only fallback test + metrics |

---

**Remaining open item:** JT-Q2 exact `raw_response_text` for 06:26 incident — close in **T0** via manifest query.

**Next step:** `create-execution-plan` → [waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md](./waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md) — **done** → `execution-peer-review` → `phase-execution`.
