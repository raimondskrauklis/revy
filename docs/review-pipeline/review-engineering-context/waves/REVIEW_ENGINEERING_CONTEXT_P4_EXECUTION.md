# Review engineering context P4 — Judge lock reuse (execution)

Phase **P4** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: RCX-G6. **P4 only.**

**Goal:** Judge escalation prompts include extracted lock IDs from same `EngineeringContextPack` path.

## Decisions locked for P4

- Reuse `build_engineering_context_pack` (or cached pack per review run if already built in P2 — prefer single fetch per run: pass pack from review task into judge task via review_run metadata or re-fetch with same SHA; **re-fetch acceptable** if simpler).
- Add bounded lock block to judge user prompt in `judge_prompt_context.py` or `_build_judge_prompt` — max 2k chars from `extracted_text`; do not change outcome schema or `parse_judge_outcome`.
- Optional judge manifest field per candidate: `lock_ids_cited: list[str]` when block included.
- No change to snippet-first policy (JC-D4) or judge-json-contract persistence gates.

## Out of scope for P4

- Moonshot prompt changes → frozen at P2
- Greptile / SSOT → **P3**

---

## P4.1 — Judge prompt lock section

**What:** `format_judge_engineering_context(pack) -> str | None`; append after evidence snippet tier, before patch fallback rules.

**Files:** `backend/app/services/judge_prompt_context.py`, `backend/app/services/github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "judge_prompt or engineering" -q
```

---

## P4.2 — Wire pack into judge escalation path

**What:** On judge run, resolve `head_sha` from revision; call pack builder when scope matches; skip silently when pack empty.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/app/workers/review_tasks.py` (if needed)

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
