# Judge JSON contract P3 — Structured output + parse fallback (execution)

Phase **P3** of [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](../JUDGE_JSON_CONTRACT_GENERAL_PLAN.md). Baseline: JC-1, JC-4, G2, G4. **P3 only.** Requires **P0** feasibility lock and **P1** observability.

**Goal:** Schema-guaranteed judge JSON on Anthropic Messages API with safe fallback parse when structured output unavailable.

## Decisions locked for P3

- Shared helper: `parse_llm_json_object(text: str) -> dict` in `anthropic_review.py` — strip markdown fences, extract first `{...}` object, `json.loads`; raise `ValueError` with stable code on failure.
- `judge_finding()`: when findings § **P0 smoke results** gateway structured row = pass **and** `settings.revy_judge_structured_output` is `True` (env `REVY_JUDGE_STRUCTURED_OUTPUT`, default `False`), send `output_config` / `json_schema`; on `400`/unsupported from gateway, fall back to plain prompt + `parse_llm_json_object` on response text (one attempt per profile, not P4 retry).
- `parse_judge_outcome(raw: dict)` unchanged — enum gate after parse.
- Bedrock path: use structured output equivalent when `bedrock_review.judge_finding` supports it; else `parse_llm_json_object` on text body — same tests mock both paths via `llm_dispatch`.
- P0 matrix **off** for structured output: P3 still ships `parse_llm_json_object` wired into existing `json.loads(text)` path.
- Moonshot `complete_review` unchanged.

## Out of scope for P3

- Second retry with error in prompt → **P4**
- Moonshot ingest changes

---

## P3.1 — `parse_llm_json_object` helper

**What:** Implement fence strip + first-object extraction; unit tests for bare JSON, ```json fences, leading prose, invalid outcome left to `parse_judge_outcome`.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "parse_llm_json" -q
```

---

## P3.2 — Structured output on `judge_finding`

**What:** Wire `output_config.format` when `settings.revy_judge_structured_output` is `True` and findings P0 matrix gateway row = pass; add `revy_judge_structured_output: bool = False` to `Settings` + `backend/.env.example` (`REVY_JUDGE_STRUCTURED_OUTPUT`).

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/app/core/config.py`, `backend/.env.example`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "judge_finding" -q
```

---

## P3.3 — Wire parse fallback in judge loop

**What:** Replace bare `json.loads` in `judge_finding` with `parse_llm_json_object`; discovery + verification paths inherit via `call_judge_llm`.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/app/integrations/bedrock_review.py` (if text path), `backend/tests/unit/test_anthropic_review.py`, `backend/tests/unit/test_bedrock_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_bedrock_review.py -q
```

---

## P3.4 — End-to-end judge unit path

**What:** Mock HTTP 200 with fenced JSON body → outcome row persisted + artifact `outcome` set in `test_github_finding_judge.py`.

**Files:** `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_bedrock_review.py tests/unit/test_github_finding_judge.py -q
pipenv run ruff check app/integrations/anthropic_review.py app/integrations/bedrock_review.py app/core/config.py
```

**Next:** [JUDGE_JSON_CONTRACT_P4_EXECUTION.md](./JUDGE_JSON_CONTRACT_P4_EXECUTION.md)
