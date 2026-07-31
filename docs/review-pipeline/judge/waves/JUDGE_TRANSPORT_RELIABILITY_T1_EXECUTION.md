# docs/review-pipeline/judge/waves/JUDGE_TRANSPORT_RELIABILITY_T1_EXECUTION.md

# T1 — Worker-visible transport logging (execution)

Phase **T1** of [JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md](../JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md). Baseline: [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](../JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md) JT-1, JT-2, JT-4. **T1 only.**

**Goal:** Celery worker tail shows judge profile, endpoint, latency, usage, and failure class without DB or `LOG_FORMAT=json`.

## Decisions locked for T1

- Log event names: `judge_llm_request_started`, `judge_llm_request_completed`, `judge_llm_profile_fallback` (retire or alias `anthropic_profile_failed_trying_fallback` on judge path).
- `judge_llm_request_started`: emitted before `client.post` in judge profile loop — surfaces in-flight attempt and URL when connection hangs or fails before httpx INFO.
- Fields: `profile`, `messages_url`, `model_id`, `duration_ms`, `input_tokens`, `output_tokens` (when present in response JSON), `outcome` or `parse_error`, `response_chars`.
- Never log full `user_prompt` or `raw_response_text` at INFO — manifest/DB retains those.
- Bedrock judge path unchanged; no Bedrock-specific transport logs in T1 unless zero-cost passthrough.
- Judge HTTP logging scoped to `_post_judge_with_profile_fallback` / `_post_judge_messages_for_profile` — not review `complete_review` path.
- Changes concentrated in `anthropic_review.py`; extend `_judge_failure_log_extra` (`github_finding_judge.py:137`) with transport fields at discovery + Pass 3 call sites.

## PR review context (first code commit — T1.0)

- **SSOT:** `.revy/review-context.json` — `active_program`: judge transport reliability; `programs[]` one entry; scope + three doc paths (execution index, findings, general plan).
- **Greptile:** `cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --write`
- **Bugbot:** `.cursor/BUGBOT.md` — active program + doc links

## Out of scope for T1

- Gateway parse → direct fallback → **T2**
- `LOG_FORMAT=json` droplet toggle → **T3** ops note
- Prometheus / Sentry → parking lot

---

## T1.0 — Program PR review context

**What:** Set `.revy/review-context.json`, regenerate `.greptile/files.json`, update `.cursor/BUGBOT.md`.

**Files:** `.revy/review-context.json`, `.greptile/files.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --write --check
pipenv run pytest tests/unit/test_generate_greptile_files.py -q
```

---

## T1.1 — Usage extraction helper

**What:** Add `_extract_usage_fields(data: dict) -> dict` in `anthropic_review.py` (input/output tokens when `usage` block present). No logging yet.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k usage -q
```

---

## T1.2 — Judge request started logging

**What:** Log `judge_llm_request_started` at entry to judge profile HTTP attempt (`_post_judge_messages_for_profile` or `_post_judge_with_profile_fallback`) with `profile`, `messages_url`, `model_id`.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k judge_llm_request_started -q
```

---

## T1.3 — Judge HTTP completion logging

**What:** After successful `client.post` + text extraction on judge path, log `judge_llm_request_completed` with `duration_ms`, usage fields, `response_chars`.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k judge_llm_request_completed -q
```

---

## T1.4 — Profile fallback log enrichment

**What:** On profile fallback in `_post_judge_with_profile_fallback` only, log `judge_llm_profile_fallback` with `profile`, `messages_url`, `error` (`failure_class` wired in **T2**).

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "judge_llm_profile_fallback or judge_finding" -q
```

---

## T1.5 — Failure log extras at call sites

**What:** Thread last transport context into `_judge_failure_log_extra` (contextvar or return metadata); apply to `github_finding_judge_failed` and `verification_judge_failed`.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/app/services/github_finding_closure.py`, `backend/tests/unit/test_github_finding_judge.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "judge_failed or failure_log" tests/unit/test_github_finding_closure.py -k verification_judge -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_github_finding_judge.py tests/unit/test_github_finding_closure.py tests/unit/test_generate_greptile_files.py -q
pipenv run ruff check app/integrations/anthropic_review.py app/services/github_finding_judge.py app/services/github_finding_closure.py
```

**Next:** [JUDGE_TRANSPORT_RELIABILITY_T2_EXECUTION.md](./JUDGE_TRANSPORT_RELIABILITY_T2_EXECUTION.md)
