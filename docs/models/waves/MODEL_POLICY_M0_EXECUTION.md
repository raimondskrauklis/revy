# docs/models/waves/MODEL_POLICY_M0_EXECUTION.md

# M0 — Model role foundations (execution)

Phase **M0** of [`MODEL_POLICY_GENERAL_PLAN.md`](../MODEL_POLICY_GENERAL_PLAN.md). Baseline: [`MODEL_POLICY_FINDINGS.md`](../MODEL_POLICY_FINDINGS.md). **M0 only.**

**Goal:** Async session-aware resolver, `model_id` through dispatch, generalized credential gates; R4/R5 refactored without behaviour change on current env.

## Decisions locked for M0

- `backend/app/services/model_policy.py` — `ModelRole`, `ModelRef`, **`async def resolve_model(session, workspace_id, role)`** (M0: env-only; `session` unused until M2).
- `backend/app/constants/model_registry.py` — **single catalog** of known `(provider, model_id)` entries; resolver defaults and M2 catalog both import this (no duplicate lists).
- Roles v1: `reviewer_standard`, `reviewer_deep`, `reviewer_critical`, `judge`.
- `ModelRef`: `provider`, `model_id`, optional `region`.
- **Reviewer provider:** `revy_reviewer_provider` (canonical). `revy_llm_provider` reads as alias when reviewer provider unset (deprecation log once).
- **Judge provider:** `revy_judge_provider` (default `anthropic`).
- **Credential gates:** `reviewer_llm_enabled()`, `judge_llm_enabled()` — replace `anthropic_api_key`-only judge skip and monolithic `llm_enabled` for pipeline gates.
- **Integrations accept `model_id`:** extend `moonshot_review.complete_review(..., model_id=)` and `anthropic_review.complete_review` / `judge_finding(..., model_id=)`; dispatch passes `ModelRef` fields (MP-D12).
- `create_review_run`: gate on `reviewer_llm_enabled()` for resolved reviewer provider; **do not** set `run.provider` at create — set in `run_review_run` from resolved `ModelRef`.
- Migration **`0022_review_run_and_judge_model_metadata`**: `github_review_runs.model_id` nullable; `github_finding_judge_outcomes.judge_provider`, `judge_model_id` nullable.
- No `workspace_model_policies` table in M0.

## Out of scope for M0

- Bedrock adapter → **M1**
- Workspace policy rows / API → **M2**
- Settings UI → **M3**

---

## M0.1 — Types + model registry

**What:** `ModelRole` enum; `ModelRef` dataclass; `model_registry.py` with platform default entries (Moonshot profile models, `claude-sonnet-5`, etc.).

**Files:** `backend/app/constants/model_policy.py` (or enums), `backend/app/constants/model_registry.py`, `backend/app/services/model_policy.py`

**Deliverable:** `cd backend && pipenv run python -c "from app.services.model_policy import ModelRole, ModelRef, resolve_model"`

---

## M0.2 — Config: reviewer/judge providers + enabled helpers

**What:** Add `revy_reviewer_provider`, `revy_judge_provider`; `reviewer_llm_enabled()`, `judge_llm_enabled()`; `revy_llm_provider` property aliases reviewer provider; update `.env.example`.

**Files:** `backend/app/core/config.py`, `backend/.env.example`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_model_policy.py -k enabled -q` — green.

---

## M0.3 — Async platform resolver

**What:** `async def resolve_model(session, workspace_id, role) -> ModelRef` — env branch only; map reviewer roles via `revy_reviewer_provider` + profile model env vars or registry; judge via `revy_judge_provider`; raise `ServiceUnavailableError` when credentials missing for resolved provider.

**Files:** `backend/app/services/model_policy.py`, `backend/tests/unit/test_model_policy.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_model_policy.py::test_resolve_platform_defaults -q` — green.

---

## M0.4 — Dispatch + integration `model_id` parameter

**What:** `llm_dispatch.py` — `call_review_llm` / `call_judge_llm` pass `model_ref.model_id` (and `region` where relevant) into integrations; update `moonshot_review` + `anthropic_review` signatures.

**Files:** `backend/app/integrations/llm_dispatch.py`, `backend/app/integrations/moonshot_review.py`, `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_moonshot_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_model_policy.py -k dispatch tests/unit/test_moonshot_review.py tests/unit/test_anthropic_review.py -q` — green.

---

## M0.5 — Migration + execution-time metadata

**What:** Hand-written `0022` adds `model_id` on review runs, `judge_provider` + `judge_model_id` on judge outcomes. `run_review_run` sets `run.provider` + `run.model_id` after resolve; judge loop persists judge model columns.

**Files:** `backend/alembic/versions/…_0022_review_run_and_judge_model_metadata.py`, `backend/app/models/github_review_run.py`, `backend/app/models/github_finding_judge_outcome.py`, `backend/app/services/github_review.py`, `backend/app/services/github_finding_judge.py`

**Deliverable:** `cd backend && pipenv run alembic upgrade head` — applies cleanly.

**LOOP pause:** after migration commit.

---

## M0.6 — Pipeline refactor + regression tests

**What:** `github_review` uses `await resolve_model` + dispatch; `create_review_run` uses `reviewer_llm_enabled()`; `github_finding_judge` uses `judge_llm_enabled()` (not raw Anthropic key). Full unit regression.

**Files:** `backend/app/services/github_review.py`, `backend/app/services/github_finding_judge.py`, `backend/tests/unit/test_github_review.py`, `backend/tests/unit/test_github_finding_judge.py`, `backend/tests/unit/test_model_policy.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_model_policy.py tests/unit/test_github_review.py tests/unit/test_github_finding_judge.py -q` — green.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint
pipenv run alembic upgrade head
pipenv run pytest tests/unit/test_model_policy.py tests/unit/test_github_review.py tests/unit/test_github_finding_judge.py tests/unit/test_moonshot_review.py tests/unit/test_anthropic_review.py -q
```

**Next:** [`MODEL_POLICY_M1_EXECUTION.md`](./MODEL_POLICY_M1_EXECUTION.md)
