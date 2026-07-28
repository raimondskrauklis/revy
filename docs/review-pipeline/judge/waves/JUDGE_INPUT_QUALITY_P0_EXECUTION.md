# Judge input quality P0 — Evidence & hunk primitives (execution)

Phase **P0** of [JUDGE_INPUT_QUALITY_GENERAL_PLAN.md](../JUDGE_INPUT_QUALITY_GENERAL_PLAN.md). Baseline: [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](../JUDGE_INPUT_INVESTIGATION_FINDINGS.md) J-1, J-2, J-3, J-11. **P0 only.**

**Goal:** Shared helpers for file-patch lookup, evidence snippets (including deleted hunk lines), and judge-scoped code context.

## Decisions locked for P0

- `JUDGE_FILE_PATCH_MAX_CHARS = 8192` (calibration in P5 if staging shows need).
- `EVIDENCE_SNIPPET_MAX_CHARS` stays 2048 until P2 widens context lines.
- `normalize_patch_file_key(path)` — forward slashes, strip leading `./`; used for all `patches_by_file` lookups.
- `extract_evidence_from_patch` includes `-` lines when they fall in the anchored window (removed-code findings).
- `resolve_judge_code_context(...)` returns `JudgeCodeContext(snippet, file_patch)` — snippet from existing resolve path; `file_patch` = truncated full file patch when path matches.
- Compare re-fetch helper **not** in P0 — **P3**.

## PR review context (first commit)

- **Greptile:** `.greptile/files.json` — `docs/review-pipeline/judge/**`, `scope: ["backend/**"]`
- **Bugbot:** `.cursor/BUGBOT.md` — links to judge findings + this execution index

## Out of scope for P0

- Verifier prompt strings → **P1**
- Wider context lines / `start_line` coercion → **P2**
- Judge task compare reload → **P3**
- PR body → **P4**

---

## P0.1 — Program PR review context

**What:** Point `.greptile/files.json` and `.cursor/BUGBOT.md` at `docs/review-pipeline/judge/` program docs.

**Files:** `.greptile/files.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
python -m json.tool .greptile/files.json > /dev/null
```

---

## P0.2 — Patch key normalization + caps

**What:** Add `normalize_patch_file_key(file_path: str) -> str` and constants `JUDGE_FILE_PATCH_MAX_CHARS` beside existing evidence constants in `github_review.py`.

**Files:** `backend/app/services/github_review.py`, `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k normalize_patch_file_key -q
```

---

## P0.3 — Deleted-line evidence extraction (J-11)

**What:** Update `extract_evidence_from_patch` to collect `-` lines in the target window (prefix with `-` in snippet or bare line — match existing style in tests). Keep `+` and context lines behavior.

**Files:** `backend/app/services/github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k evidence -q
```

---

## P0.4 — `resolve_judge_code_context`

**What:** Add dataclass `JudgeCodeContext` and `resolve_judge_code_context(file_path, start_line, patches_by_file, supplemental_top_by_file)` using normalized path key; delegate snippet to `resolve_evidence_snippet`; attach capped file patch when patch exists.

**Files:** `backend/app/services/github_review.py`, `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k resolve_judge_code_context -q
```

---

## P0.5 — Unit tests (primitives + judge candidate alignment)

**What:** Tests: deleted-line snippet; line-less finding still gets file patch in context; missing patch → empty patch; `normalize_patch_file_key` path variants. Add test that `is_judge_candidate` on finding matches group fields used in `_load_judge_candidates` (severity/category from finding row).

**Files:** `backend/tests/unit/test_github_review.py`, `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k "normalize_patch_file_key or resolve_judge_code_context or evidence or patch" tests/unit/test_github_finding_judge.py -k judge_candidate -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_review.py tests/unit/test_github_finding_judge.py -q
pipenv run ruff check app/services/github_review.py
```

**Next:** [JUDGE_INPUT_QUALITY_P1_EXECUTION.md](./JUDGE_INPUT_QUALITY_P1_EXECUTION.md)
