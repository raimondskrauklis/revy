# Judge JSON contract P4 — Targeted retry (execution)

Phase **P4** of [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](../JUDGE_JSON_CONTRACT_GENERAL_PLAN.md). Baseline: G5. **P4 only.** Requires **P3** on staging sample.

**Goal:** Recover residual parse failures with max **one** retry per candidate — no retry storms.

## Decisions locked for P4

- Retry triggers: `ValueError` from `parse_llm_json_object` or `parse_judge_outcome` only — not `httpx` transport errors (those stay single-attempt + P1 artifact).
- Retry prompt: append user message with `parse_error` + schema reminder (`outcome` enum).
- Max 1 retry per candidate per run — `retry_count` field on `JudgeCandidateArtifact` (0 default, 1 if retried).
- **Skip phase** when operator records ≥95% outcome persistence on P3 staging dogfood — commit updates validation memo § P4 skipped with evidence; no retry code.
- Discovery and verification judge loops both honor retry policy.
- No second model; no outcome enum change.

## Out of scope for P4

- Unbounded retries
- RG-6 relaxation

---

## P4.0 — Staging sample gate (operator)

**What:** Before coding, check P3 staging metrics — if ≥95% candidates → outcome row, document skip in memo and jump to P4.4 doc-only.

**Files:** `JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md` (create stub if missing)

**Deliverable (non-gate):** Memo row: P4 required yes/no with date.

---

## P4.1 — Retry wrapper in `judge_finding` call site

**What:** Extract `_call_judge_with_optional_retry` used by discovery + verification loops; passes through to `llm_dispatch.call_judge_llm` with retry on parse contract failure only.

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

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_finding_closure.py tests/unit/test_github_pipeline_trace.py -q
```

**Deploy:** ship with P3 before staging re-measure.

**Next:** [JUDGE_JSON_CONTRACT_P5_EXECUTION.md](./JUDGE_JSON_CONTRACT_P5_EXECUTION.md)
