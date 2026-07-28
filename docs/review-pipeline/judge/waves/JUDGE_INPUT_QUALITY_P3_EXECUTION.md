# Judge input quality P3 — Scoped context in judge step (execution)

Phase **P3** of [JUDGE_INPUT_QUALITY_GENERAL_PLAN.md](../JUDGE_INPUT_QUALITY_GENERAL_PLAN.md). Baseline: [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](../JUDGE_INPUT_INVESTIGATION_FINDINGS.md) J-1, J-6, J-8. **P3 only.**

**Goal:** Each judge candidate gets capped **file patch** + evidence snippet in prompt; patches re-fetched at judge time via GitHub compare.

## Decisions locked for P3

- **Compare pair:** `base_sha=revision.base_sha`, `head_sha=revision.head_sha` — same as `prepare_review_context` / `_fetch_compare_for_review`. **Not** `prior_revision.head_sha` delta from resolution metrics.
- Shared helper `fetch_compare_patches_by_file(session, pull_request, revision) -> dict[str, str]` in **`backend/app/services/github_compare_patches.py`** (new module).
- Judge loads patches once per review run in `record_review_run_judge_status` before `_run_judge_llm_loop`.
- `_build_judge_prompt(..., file_patch: str | None)` adds block `File diff (scoped):` capped by `JUDGE_FILE_PATCH_MAX_CHARS`.
- `JudgeCandidateArtifact` adds `file_patch_chars: int | None`; `record_judge_pipeline_step` manifest includes `file_patch_chars` per candidate.
- Do **not** parse truncated review prompt artifact for patches.

- `revision.base_sha` nullable — empty `patches_by_file` on `missing_base_sha` (same as review compare fallback).

## Out of scope for P3

- Full unified diff in judge prompt
- Persist `patches_by_file` on review manifest (fallback only if P5 staging blocks on compare cost)

---

## P3.1 — Compare patch fetch helper (J-8)

**What:** Create `backend/app/services/github_compare_patches.py` with `fetch_compare_patches_by_file` using installation token + `compare_commits(base_sha=revision.base_sha, head_sha=revision.head_sha)`; return `{filename: patch}`; log compare failures like resolution metrics.

**Files:** `backend/app/services/github_compare_patches.py`, `backend/tests/unit/test_github_compare_patches.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_compare_patches.py -q
```

---

## P3.2 — Load patches at judge entry

**What:** In `record_review_run_judge_status`, load review run + revision + pull_request; call `fetch_compare_patches_by_file`; pass `patches_by_file` into `_run_judge_llm_loop`. Empty dict on compare failure — judge still runs with stored `evidence_snippet` only.

**Files:** `backend/app/services/github_finding_judge.py`

**Deliverable:** Covered by P3.5 pytest (mock fetch + judge loop); ruff:

```bash
cd backend && pipenv run ruff check app/services/github_finding_judge.py
```

---

## P3.3 — Patch block in judge prompt

**What:** Extend `_build_judge_prompt` with optional `file_patch`; use `resolve_judge_code_context` from P0 when building per candidate. Wire `file_patch` from context into prompt assembly in `_run_judge_llm_loop`.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/app/services/github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "judge_prompt or file_patch" -q
```

---

## P3.4 — Trace manifest fields (J-6)

**What:** Add `file_patch_chars` to `JudgeCandidateArtifact` and judge step manifest JSON (`record_judge_pipeline_step` candidate payload).

**Files:** `backend/app/services/github_finding_judge.py`, `backend/app/services/github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py -k judge -q
```

---

## P3.5 — Unit tests (reload + assembly)

**What:** Mock `fetch_compare_patches_by_file` in judge tests; assert user prompt contains `File diff` when patch returned; assert `file_patch_chars` in artifact; compare failure → no patch block but verifier header still present.

**Files:** `backend/tests/unit/test_github_finding_judge.py`, `backend/tests/unit/test_github_compare_patches.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_compare_patches.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_compare_patches.py tests/unit/test_github_pipeline_trace.py -q
pipenv run ruff check app/services/github_finding_judge.py app/services/github_compare_patches.py
```

**Next:** [JUDGE_INPUT_QUALITY_P4_EXECUTION.md](./JUDGE_INPUT_QUALITY_P4_EXECUTION.md)
