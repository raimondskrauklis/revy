# Review engineering context P2 — Moonshot inject (execution)

Phase **P2** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: RCX-D8, D12, G2. **P2 only.**

**Goal:** `prepare_review_context` prepends engineering block; wire config caps; populate retrieve manifest + `context_stats`.

## Decisions locked for P2

- Replace `DIFF_MAX_BYTES` / `PR_BODY_MAX_BYTES` module constants usage in `github_review.py` with `settings.revy_diff_max_bytes` / `settings.revy_pr_body_max_bytes`.
- Call `build_engineering_context_pack` when installation + repo + head_sha available; pass `changed_files`, `omitted_files`, `patches_by_file` for dedupe.
- **Dedupe (RCX-D12):** for each manifest path `p`, skip appending full fetched MD to inject body when `p in changed_files` and `p not in omitted_files` and compare patch exists; **always** include merged `extracted_text` (locks/smoke).
- `_build_review_prompt`: new section `Engineering context (authoritative):` before `Unified diff`; instruction line: treat engineering block over generic API prior.
- After `prepare_review_context` in review worker: persist `context_stats` on `GitHubReviewRunORM` before Moonshot call; retrieve-step manifest merged in `record_retrieve_pipeline_step` (existing hook after context pack built).
- `engineering_context_injected=true` when pack has non-empty `extracted_text` or non-deduped body.

## Out of scope for P2

- Greptile `files.json` generator → **P3**
- Judge → **P4**

---

## P2.1 — Config-driven diff and PR body caps

**What:** `build_unified_diff` and `_build_review_prompt` use settings; tests assert 512 KB default changes truncation behavior vs 128 KB fixture.

**Files:** `backend/app/services/github_review.py`, `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k "unified_diff or truncate" -q
```

---

## P2.2 — Dedupe helper

**What:** `should_skip_full_md_inject(path, changed_files, omitted_files, patches_by_file) -> bool` per RCX-D12 table.

**Files:** `backend/app/services/engineering_context/dedupe.py`, `backend/tests/unit/test_engineering_context_dedupe.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_engineering_context_dedupe.py -q
```

---

## P2.3 — Prompt inject block

**What:** `_format_engineering_context_block(pack) -> str`; integrate into `_build_review_prompt` before diff; update review instruction string.

**Files:** `backend/app/services/github_review.py`, `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k "build_review_prompt or engineering_context" -q
```

---

## P2.4 — Wire `prepare_review_context`

**What:** Fetch pack at `head_sha`; pass block into prompt builder; handle loader errors (empty pack, log, `engineering_context_injected=false`).

**Files:** `backend/app/services/github_review.py`, `backend/app/workers/review_tasks.py` (if stats persist on run), `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k "prepare_review_context" -q
```

---

## P2.5 — Manifest + `context_stats` populate

**What:** Merge engineering fields into `build_retrieval_manifest`; `record_retrieve_pipeline_step` receives populated dict; helper `build_context_stats(pack, prompt_chars, diff_meta) -> dict` writes ORM column.

**Files:** `backend/app/services/engineering_context/stats.py`, `backend/app/services/github_pipeline_trace.py`, `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py tests/unit/test_github_review.py -k "context_stats or engineering_context" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/services/github_review.py app/services/engineering_context/
pipenv run pytest tests/unit/test_engineering_context_dedupe.py tests/unit/test_github_review.py tests/unit/test_github_pipeline_trace.py -q
```

**Next:** [REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md)
