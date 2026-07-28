# Judge JSON contract P1 — Failure observability (execution)

Phase **P1** of [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](../JUDGE_JSON_CONTRACT_GENERAL_PLAN.md). Baseline: findings G1, JC-2. **P1 only.**

**Goal:** Every judge candidate attempt leaves an auditable trace — success or failure body — in pipeline manifest and structured logs.

## Decisions locked for P1

- Extend `JudgeCandidateArtifact` dataclass: `raw_response_text: str | None`, `parse_error: str | None` (keep `raw_response: dict | None` on success).
- On parse/HTTP failure: set `raw_response_text` from response body (truncated same as review raw_response cap in `github_pipeline_trace`); set `parse_error` to exception message; `raw_response=None`, `outcome=None`.
- On success: `parse_error=None`; `raw_response_text` optional (omit or mirror serialized dict — **omit** to save bytes; parsed dict stays in `raw_response`).
- Apply to **discovery** (`github_finding_judge.py`) and **verification** (`github_finding_closure.py` verification judge loop).
- `record_judge_pipeline_step` manifest JSON includes new fields per candidate — no DB migration.
- Structured log `github_finding_judge_failed` adds `parse_error` and `response_chars` when body captured.
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

## P1.2 — Discovery judge failure capture

**What:** In `record_review_run_judge_status`, on except path capture `text` from `ValueError`/`json` failures and HTTP response body when available; populate artifact fields; enrich logger `extra`.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "judge_failed or artifact" -q
```

---

## P1.3 — Verification judge failure capture

**What:** Mirror P1.2 in `verify_still_open_escalation_groups` verification judge loop — same artifact shape.

**Files:** `backend/app/services/github_finding_closure.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -k "verification" -q
```

---

## P1.4 — Manifest contract test

**What:** Unit test asserts failed candidate manifest entry has non-null `parse_error` and no silent `raw_response=null` without `parse_error` on HTTP 200 parse fail (mock `judge_finding` returning invalid JSON string path).

**Files:** `backend/tests/unit/test_github_finding_judge.py`, `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_pipeline_trace.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_finding_closure.py tests/unit/test_github_pipeline_trace.py -q
pipenv run ruff check app/services/github_finding_judge.py app/services/github_finding_closure.py app/services/github_pipeline_trace.py
```

**Next:** [JUDGE_JSON_CONTRACT_P2_EXECUTION.md](./JUDGE_JSON_CONTRACT_P2_EXECUTION.md)
