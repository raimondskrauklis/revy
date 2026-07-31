# docs/review-pipeline/judge/waves/JUDGE_TRANSPORT_RELIABILITY_T2_EXECUTION.md

# T2 — Gateway profile fallback hardening (execution)

Phase **T2** of [JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md](../JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md). Baseline: [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](../JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md) JT-3. **T2 only.**

**Goal:** Gateway down **or** gateway garbage response → try direct Anthropic in the same `judge_finding` call; preserve `call_judge_with_optional_retry` parse retry after a profile returns text.

## Decisions locked for T2

- Fallback triggers on gateway profile only: `httpx.HTTPError`, `ServiceUnavailableError` (empty/invalid body), `JudgeParseError`.
- At most **one** step to next profile per `judge_finding` invocation (gateway → direct); no multi-hop beyond existing profile list.
- `call_judge_with_optional_retry` unchanged in contract — still retries parse on **successful** text from chosen profile chain.
- `failure_class` on `judge_llm_profile_fallback`: `http` | `empty_body` | `parse`.
- Profile order unchanged: gateway first, direct second.
- **Parse moves into profile loop:** today `judge_finding` calls `parse_judge_payload` after `_post_judge_with_profile_fallback` returns text (`anthropic_review.py:387–395`); T2 parses per profile inside the loop so gateway parse failure can try direct.

## Out of scope for T2

- Transport logging additions beyond T1 → already shipped
- Bedrock fallback chain
- `REVY_JUDGE_STRUCTURED_OUTPUT` → parking lot
- Changing `resolve_model` or gateway model id policy

---

## T2.1 — Parse-in-profile-loop refactor

**What:** Refactor `_post_judge_with_profile_fallback` (or `judge_finding`) so each profile: POST → extract text → `parse_judge_payload` before advancing. Gateway failures classified; do not return text to outer `judge_finding` parse. `_post_judge_messages_for_profile` already exists (`anthropic_review.py:241`) — extend loop, do not re-extract.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k judge_finding -q
```

Behavior unchanged for direct-only config until T2.2–T2.3 tests land.

---

## T2.2 — Empty-body gateway fallback

**What:** When `_extract_message_text` raises `ServiceUnavailableError` on gateway profile, catch and try direct profile with `failure_class=empty_body`.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "empty_body or gateway_fallback" -q
```

---

## T2.3 — Gateway parse-fail fallback

**What:** When `parse_judge_payload` raises `JudgeParseError` after gateway HTTP 200, try direct profile before surfacing error; `failure_class=parse`. Direct-only config unchanged (no infinite loop).

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "parse_fallback or judge_finding" -q
```

---

## T2.4 — Integration with `call_judge_with_optional_retry`

**What:** Unit test: gateway returns invalid JSON → direct returns valid outcome; assert `call_judge_with_optional_retry` succeeds with `retry_count=0`.

**Files:** `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "gateway_parse_fallback or call_judge_with_optional_retry" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_github_finding_judge.py -q
pipenv run ruff check app/integrations/anthropic_review.py
```

**Deploy:** Ship T1+T2 together or T2 immediately after T1 on same branch.

**Next:** [JUDGE_TRANSPORT_RELIABILITY_T3_EXECUTION.md](./JUDGE_TRANSPORT_RELIABILITY_T3_EXECUTION.md)
