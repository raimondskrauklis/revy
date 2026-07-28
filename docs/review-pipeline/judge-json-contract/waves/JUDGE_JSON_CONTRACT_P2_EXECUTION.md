# Judge JSON contract P2 — Snippet-first prompt policy (execution)

Phase **P2** of [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](../JUDGE_JSON_CONTRACT_GENERAL_PLAN.md). Baseline: findings JC-D4, G3. **P2 only.** Requires **P1** deployed for `user_prompt` / `file_patch_chars` measurement.

**Goal:** Restore find→verify context size — ~1k prompts when snippet exists; patch only as fallback (~2k cap).

## Decisions locked for P2

- When `evidence_snippet` is non-empty after strip: **do not** attach `file_patch` to discovery or verification judge prompts.
- Tier 2 — line anchor present, snippet empty/thin: attach truncated patch only (`JUDGE_FILE_PATCH_MAX_CHARS = 2048`).
- Tier 3 — no line anchor: patch fallback with same 2048 cap (down from 8192).
- `build_verification_judge_prompt` in `anthropic_review.py` follows same tier rules as `_build_judge_prompt`.
- `file_patch_chars` in artifact: `None` when patch omitted; `len(patch)` when included.
- `resolve_judge_code_context` unchanged — truncation happens at prompt assembly layer.
- No change to Moonshot review prompt assembly.

## Out of scope for P2

- Structured output → **P3**
- Parse helper → **P3**

---

## P2.1 — Discovery prompt tiers

**What:** Refactor `_build_judge_prompt` — snippet-first branch; patch cap constant; unit tests per tier (snippet only, snippet+patch forbidden, patch-only fallback).

**Files:** `backend/app/services/github_finding_judge.py`, `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "prompt or build_judge" -q
```

---

## P2.2 — Verification prompt tiers

**What:** Align `build_verification_judge_prompt` with P2.1 rules — skip push delta patch when evidence excerpt present; cap patch at 2048.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "verification" -q
```

---

## P2.3 — Integration assertion on prompt size

**What:** Test fixture: group with snippet + 8k patch context available → assembled `user_prompt` len < 2500 and `file_patch_chars` is None in artifact path (mock judge).

**Files:** `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "prompt_size or snippet" -q
```

---

## P2.4 — Findings addendum prompt metrics

**What:** Add note in findings § staging metrics — expected p50 drop after P2 deploy (operator fills post-staging).

**Files:** `docs/review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md`

**Deliverable:** Findings § references P2 prompt policy with before/after placeholder.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_anthropic_review.py -q
pipenv run ruff check app/services/github_finding_judge.py app/integrations/anthropic_review.py
```

**Next:** [JUDGE_JSON_CONTRACT_P3_EXECUTION.md](./JUDGE_JSON_CONTRACT_P3_EXECUTION.md)
