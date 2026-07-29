# Review engineering context P4 — Judge lock reuse (execution)

Phase **P4** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: RCX-G6. **P4 only.**

**Goal:** Judge escalation prompts include extracted lock IDs from same `EngineeringContextPack` path.

## Decisions locked for P4

- **No cached pack from Moonshot** — judge path **re-fetches** via `build_engineering_context_pack` in one httpx client scope: `compare_commits` → `changed_files` from `compare.paths_to_index`; `omitted_files` from `build_unified_diff(compare.files, max_bytes=settings.revy_diff_max_bytes)` (not from compare alone); `patches_by_file` from compare patches. Judge prompt uses **`extracted_text` only** (2048 cap) — dedupe inputs still passed for pack parity with P2.
- Judge lock block: **max 2048 chars** from `extracted_text` (tighter than Moonshot `revy_engineering_context_max_bytes` default 32k — intentional).
- Wire into `_build_judge_prompt` in `github_finding_judge.py` and helpers in `judge_prompt_context.py`.
- Optional judge manifest field per candidate: `lock_ids_cited: list[str]` when block included.
- No change to snippet-first policy (JC-D4) or judge-json-contract persistence gates.

## Out of scope for P4

- Moonshot prompt changes → frozen at P2
- Greptile / SSOT → **P3**

---

## P4.1 — Judge prompt lock section

**What:** `format_judge_engineering_context(pack, *, max_chars=2048) -> str | None`; integrate in `_build_judge_prompt` after evidence snippet tier, before patch fallback.

**Files:** `backend/app/services/judge_prompt_context.py`, `backend/app/services/github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "judge_prompt or engineering" -q
```

---

## P4.2 — Wire pack into judge escalation path

**What:** In judge escalation (`record_review_run_judge_status` / `_run_judge_llm_loop` entry): resolve installation/owner/repo; single client block — `compare_commits`, `build_unified_diff` for `omitted_files`, then `build_engineering_context_pack`; pass pack into `_build_judge_prompt`.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/app/services/github_compare_patches.py` (reuse if applicable)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -q
```

---

## P4.3 — Manifest `lock_ids_cited` + regression guard

**What:** Add optional field to judge candidate artifact serialization; test judge-json-contract persistence path unchanged.

**Files:** `backend/app/services/github_pipeline_trace.py`, `backend/tests/unit/test_github_finding_judge.py`, `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_pipeline_trace.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/services/judge_prompt_context.py app/services/github_finding_judge.py
pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_pipeline_trace.py -q
```

**Next:** [REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md)
