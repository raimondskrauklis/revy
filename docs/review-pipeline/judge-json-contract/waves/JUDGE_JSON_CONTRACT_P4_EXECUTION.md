# Judge JSON contract P4 — Targeted retry (execution)

Phase **P4** of [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](../JUDGE_JSON_CONTRACT_GENERAL_PLAN.md). Baseline: G5. **P4 only.** Requires **P3** on staging sample.

**Goal:** Recover residual parse failures with max **one** retry per candidate — no retry storms.

## Decisions locked for P4

- Retry triggers: `JudgeParseError` / `ValueError` from `parse_llm_json_object` or `parse_judge_outcome` only — not `httpx` transport errors (those stay single-attempt + P1 artifact).
- Retry prompt: append user message with `parse_error` + schema reminder (`outcome` enum).
- Max 1 retry per candidate per run — `retry_count` field on `JudgeCandidateArtifact` (0 default, 1 if retried).
- **Skip phase** when operator records ≥95% outcome persistence on P3 staging dogfood — **P4.4** doc-only commit; no retry code.
- Discovery and verification judge loops both honor retry policy.
- No second model; no outcome enum change.
- **Validation memo stub:** P4.0 creates `JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md` with P4 skip row; P5.3 expands same file (no duplicate).

## Out of scope for P4

- Unbounded retries
- RG-6 relaxation

---

## P4.0 — Staging sample gate (operator)

**What:** Before coding, check P3 staging metrics — if ≥95% candidates → outcome row, record in validation memo stub and proceed to **P4.4** (skip P4.1–P4.3).

**Files:** `docs/review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md` (create stub with § P4 gate table)

**Deliverable (non-gate):** Memo row: P4 required yes/no with date.

---

## P4.1 — Retry wrapper in judge loops

**What:** Extract `_call_judge_with_optional_retry` used by `_run_judge_llm_loop` and verification judge loop; passes through to `llm_dispatch.call_judge_llm` with retry on parse contract failure only.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/app/services/github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "retry" -q
```

---

## P4.2 — Artifact `retry_count`

**What:** Populate `retry_count` on `JudgeCandidateArtifact`; manifest serialization in `github_pipeline_trace.py`.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/app/services/github_pipeline_trace.py`, `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py -q
```

---

## P4.3 — Verification retry parity test

**What:** Unit test verification judge path retries once on invalid JSON then succeeds.

**Files:** `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -k "verification and retry" -q
```

---

## P4.4 — Doc-only skip (when P4.0 gate passes)

**What:** When P3 staging ≥95% outcome persistence: update validation memo § P4 skipped with evidence; update execution index P4 row status `skipped (doc-only)`; **no** retry code in this commit.

**Files:** `docs/review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md`, `docs/review-pipeline/judge-json-contract/waves/JUDGE_JSON_CONTRACT_EXECUTION.md`

**Deliverable:** Memo § P4 documents skip reason + date; execution table reflects skip.

---

**Phase gate** (from `backend/` — skip pytest additions when P4.4 doc-only only):

```bash
pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_finding_closure.py tests/unit/test_github_pipeline_trace.py -q
pipenv run ruff check app/services/github_finding_judge.py app/services/github_finding_closure.py app/services/github_pipeline_trace.py
```

**Deploy:** ship with P3 before staging re-measure.

**Next:** [JUDGE_JSON_CONTRACT_P5_EXECUTION.md](./JUDGE_JSON_CONTRACT_P5_EXECUTION.md)
