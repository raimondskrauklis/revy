# docs/review-pipeline/judge-thinking-blocks/waves/JUDGE_THINKING_BLOCKS_P1_EXECUTION.md

# P1 — Empty text is a parse miss (execution)

Phase **P1** of [`JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md`](../JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md). Baseline: [`JUDGE_THINKING_BLOCKS_FINDINGS.md`](../JUDGE_THINKING_BLOCKS_FINDINGS.md) JTB-D4, JTB-D6, JTB-D7. **P1 only.**

**Goal:** `_post_judge_anthropic_messages` maps helper `""` → `JudgeParseError` (`judge_empty_text`) so `call_judge_with_optional_retry` runs the existing one retry. Anthropic review already maps `""` → SUE (P0). Record transport extra on that wrap so P2 is not skipped by the current `(httpx.HTTPError, ServiceUnavailableError)` except.

## Decisions locked for P1

- **Judge wrap only:** helper `""` → `JudgeParseError("judge_empty_text", response_text=…)`. Do not raise `JudgeParseError` from `_extract_message_text` (D2/D4).
- Additive code is **`judge_empty_text` only**. Do not rename live **`judge_json_invalid`**. Do not add a second JSON-invalid token (D6).
- Before raising, set judge transport extra including `content_block_types` (ordered list of `content[].type` strings). Home is the wrap + `_set_judge_transport_context` / `_record_judge_transport_failure` — today’s except at `_post_judge_anthropic_messages` ~331 does **not** catch `JudgeParseError`, so extra must be written on the wrap path explicitly.
- Keep `_post_judge_with_profile_fallback` catching `(httpx.HTTPError, ServiceUnavailableError, JudgeParseError)` — do not remove gateway→direct fallback (D7).
- Existing retry: one schema-reminder retry on `JudgeParseError` / `judge_outcome_invalid` only. No extra retries, no second model, no retry-prompt rewrite (D7).
- Review path stays SUE on `""` (P0). RG-6 unchanged.

## Out of scope for P1 (later phases)

- Manifest/metrics distinguishability polish + D8 INFO audit → **P2**
- Staging split evidence + JTB-Q5 → **P3**
- Raising `JudgeParseError` from the helper → never (locked)

---

## P1.1 — Judge wrap empty text to `judge_empty_text`

**What:** After `_extract_message_text` in `_post_judge_anthropic_messages`, if the string is `""`, raise `JudgeParseError("judge_empty_text", response_text=truncate_judge_response_text(preview))`. Success path (non-empty text) unchanged → existing `parse_judge_payload`.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/app/integrations/judge_llm_errors.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:** Thinking-only judge HTTP raises `JudgeParseError` with `.code == "judge_empty_text"`; `parse_judge_payload` invalid JSON still uses **`judge_json_invalid`**.

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "judge_empty_text or judge_json_invalid or extract_message_text" -q
```

---

## P1.2 — Transport extra on empty-text wrap

**What:** On the P1.1 wrap, write transport context **before** raise: `parse_error=judge_empty_text`, `content_block_types` (e.g. `["thinking"]` or `["thinking","text"]` when text was blank), duration/usage already collected. Do not rely on the HTTP/SUE except to record this miss.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:** After thinking-only judge call, `get_judge_transport_log_fields()` includes `parse_error=judge_empty_text` and `content_block_types`.

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "transport or judge_empty_text" -q
```

---

## P1.3 — Retry fires on empty text, not on HTTP

**What:** Extend `call_judge_with_optional_retry` tests: thinking-only first response → retry; HTTP/SUE still no retry; double empty-text → `retry_count` visible (existing `judge_retry_count` / artifact field). Do not change retry prompt beyond current schema reminder.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:** Retry-on-`judge_empty_text` vs no-retry-on-HTTP; second miss records retry count.

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "optional_retry or judge_empty_text" -q
```

---

## P1.4 — Review SUE regression + profile fallback stays

**What:** Confirm Anthropic `complete_review` / `_post_anthropic_messages` still SUE on `""`. Confirm `_post_judge_with_profile_fallback` still catches `JudgeParseError` and may try the next profile when `allow_judge_profile_fallback` is set — do not “fix” fallback away.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:** Review thinking-only → SUE; fallback unit coverage still includes `JudgeParseError`.

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "complete_review or profile_fallback or judge_empty_text" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/integrations/anthropic_review.py app/integrations/judge_llm_errors.py app/services/github_finding_judge.py
pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_github_finding_judge.py -q
```

**Deploy:** Same PR as P0. Backend + worker only; no migration.

**Next:** [`JUDGE_THINKING_BLOCKS_P2_EXECUTION.md`](./JUDGE_THINKING_BLOCKS_P2_EXECUTION.md)
