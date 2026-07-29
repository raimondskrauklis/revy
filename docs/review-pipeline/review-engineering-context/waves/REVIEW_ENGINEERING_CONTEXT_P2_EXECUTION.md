# Review engineering context P2 — Moonshot inject (execution)

Phase **P2** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: RCX-D8, D12, G2. **P2 only.**

**Goal:** `prepare_review_context` prepends engineering block; wire config caps; populate retrieve manifest + `context_stats`.

## Decisions locked for P2

- Replace `DIFF_MAX_BYTES` / `PR_BODY_MAX_BYTES` module constants in `github_review.py` with `settings.revy_diff_max_bytes` / `settings.revy_pr_body_max_bytes`.
- **Repo context for pack builder:** add `_resolve_github_repo_for_revision(session, revision, pull_request) -> (installation, owner, repo, client)` — mirror lookup in `_fetch_compare_for_review` (`github_review.py:722–736`). `prepare_review_context` calls it before `build_engineering_context_pack`.
- Call `build_engineering_context_pack` with installation, owner, repo, client, `head_sha`, `changed_files`, `omitted_files`, `patches_by_file`.
- **Dedupe (RCX-D12):** for each manifest path `p`, skip appending full fetched MD to inject body when `p in changed_files` and `p not in omitted_files` and compare patch exists; **always** include merged `extracted_text` (locks/smoke).
- `_build_review_prompt`: new section `Engineering context (authoritative):` before `Unified diff`; instruction line: treat engineering block over generic API prior.
- **`ReviewContextPack.manifest` is fully built inside `prepare_review_context`** (engineering fields included). `record_retrieve_pipeline_step` in `review_tasks.py` persists that manifest unchanged after `run_review_run` returns.
- **`context_stats` ORM persist in `run_review_run`** (`github_review.py` ~975) after `prepare_review_context`, before Moonshot LLM call — not in `review_tasks.py`.
- Extend `build_retrieval_manifest` without breaking `test_build_retrieval_manifest_includes_sc3_defaults` (SC3 stub fields preserved).
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

## P2.4 — Wire `prepare_review_context` + repo resolution

**What:** Implement `_resolve_github_repo_for_revision`; call `build_engineering_context_pack` inside `prepare_review_context`; attach pack to `ReviewContextPack` (new field or parallel return); handle loader errors (`engineering_context_injected=false`).

**Files:** `backend/app/services/github_review.py`, `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k "prepare_review_context" -q
```

---

## P2.5 — Manifest + `context_stats` populate

**What:** Merge engineering fields in `build_retrieval_manifest` inside `prepare_review_context`; `build_context_stats(pack, prompt_chars, diff_meta)`; persist `review_run.context_stats` in `run_review_run` after context prepare.

**Files:** `backend/app/services/engineering_context/stats.py`, `backend/app/services/github_review.py`, `backend/tests/unit/test_github_pipeline_trace.py`, `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k "retrieval_manifest_includes_sc3_defaults or context_stats or engineering_context" -q
pipenv run pytest tests/unit/test_github_pipeline_trace.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/services/github_review.py app/services/engineering_context/
pipenv run pytest tests/unit/test_engineering_context_dedupe.py tests/unit/test_github_review.py tests/unit/test_github_pipeline_trace.py -q
```

**Next:** [REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md)
