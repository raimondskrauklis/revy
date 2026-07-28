# Judge JSON contract P1 — Failure observability (execution)

Phase **P1** of [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](../JUDGE_JSON_CONTRACT_GENERAL_PLAN.md). Baseline: findings G1, JC-2. **P1 only.**

**Goal:** Every judge candidate attempt leaves an auditable trace — success or failure body — in pipeline manifest and structured logs.

## Decisions locked for P1

- Extend `JudgeCandidateArtifact` dataclass: `raw_response_text: str | None`, `parse_error: str | None` (keep `raw_response: dict | None` on success).
- **Integration contract (locked):** `judge_finding()` in `anthropic_review.py` and `bedrock_review.py` must surface HTTP 200 response **text** on parse failure — today `json.loads(text)` runs inside integration and raises `ValueError` without the body. Introduce `JudgeParseError(ValueError)` with `response_text: str` (truncated to `_RAW_RESPONSE_MAX_BYTES` from `github_pipeline_trace`) or return a small `JudgeLlmResult(parsed: dict | None, raw_response_text: str)` — pick one pattern, use in both providers.
- `llm_dispatch.call_judge_llm` propagates the same contract to discovery + verification loops.
- On parse/HTTP failure in `_run_judge_llm_loop` / verification loop: set `raw_response_text` from `JudgeParseError.response_text` or result object; set `parse_error` to stable error code/message; `raw_response=None`, `outcome=None`.
- On success: `parse_error=None`; `raw_response_text` **omitted** (parsed dict stays in `raw_response`).
- Apply to **discovery** (`_run_judge_llm_loop` in `github_finding_judge.py`) and **verification** (`verify_still_open_escalation_groups` in `github_finding_closure.py`).
- `record_judge_pipeline_step` manifest JSON includes new fields per candidate — no DB migration.
- Structured log `github_finding_judge_failed` / `verification_judge_failed` adds `parse_error` and `response_chars` when body captured.
- RG-6 and `skipped_unavailable` logic unchanged.

## Out of scope for P1

- Structured output API → **P3**
- Snippet-first prompts → **P2**
- Retry loop → **P4**

---

## P1.1 — Extend artifact dataclass

**What:** Add `raw_response_text` and `parse_error` to `JudgeCandidateArtifact`; update `record_judge_pipeline_step` serialization in `github_pipeline_trace.py`.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/app/services/github_pipeline_trace.py`, `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py -q
```

---

## P1.2 — Integration layer parse-error contract

**What:** Refactor `judge_finding()` in `anthropic_review.py` and `bedrock_review.py` — capture response text before `json.loads`; on parse failure raise `JudgeParseError` (or return `JudgeLlmResult`) with `response_text` preserved. Update `llm_dispatch.call_judge_llm` to pass through unchanged signature for callers.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/app/integrations/bedrock_review.py`, `backend/app/integrations/llm_dispatch.py`, `backend/tests/unit/test_anthropic_review.py`, `backend/tests/unit/test_bedrock_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_bedrock_review.py -k "judge_finding or parse" -q
```

---

## P1.3 — Discovery judge failure capture

**What:** In `_run_judge_llm_loop` except path, read `response_text` from `JudgeParseError` (or result object); populate artifact `raw_response_text` + `parse_error`; enrich logger `extra`.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "judge_failed or artifact" -q
```

---

## P1.4 — Verification judge failure capture

**What:** Mirror P1.3 in `verify_still_open_escalation_groups` verification judge loop — same artifact shape and Bedrock/Anthropic parity via `call_judge_llm`.

**Files:** `backend/app/services/github_finding_closure.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -k "verification" -q
```

---

## P1.5 — Manifest contract test

**What:** Unit test: mock HTTP 200 with non-JSON body → artifact has non-null `parse_error` + `raw_response_text`, not silent `raw_response=null` alone.

**Files:** `backend/tests/unit/test_github_finding_judge.py`, `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_pipeline_trace.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_bedrock_review.py tests/unit/test_github_finding_judge.py tests/unit/test_github_finding_closure.py tests/unit/test_github_pipeline_trace.py -q
pipenv run ruff check app/integrations/anthropic_review.py app/integrations/bedrock_review.py app/integrations/llm_dispatch.py app/services/github_finding_judge.py app/services/github_finding_closure.py app/services/github_pipeline_trace.py
```

**Next:** [JUDGE_JSON_CONTRACT_P2_EXECUTION.md](./JUDGE_JSON_CONTRACT_P2_EXECUTION.md)
