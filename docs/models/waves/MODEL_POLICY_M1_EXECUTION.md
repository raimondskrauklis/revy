# docs/models/waves/MODEL_POLICY_M1_EXECUTION.md

# M1 — AWS Bedrock LLM provider (execution)

Phase **M1** of [`MODEL_POLICY_GENERAL_PLAN.md`](../MODEL_POLICY_GENERAL_PLAN.md). **M1 only.**

**Goal:** Judge (and optional reviewer) via Bedrock using platform env — resolver + dispatch only; no workspace rows, no UI.

**Depends on:** M0 PASS (including migration `0022`).

## Decisions locked for M1

- `backend/app/integrations/bedrock_review.py` — Bedrock Converse API; `complete_review` / `judge_finding` accept `model_id` + `region` (same contract as M0 dispatch).
- Config: `aws_region`; `revy_bedrock_judge_model_id`; **`revy_bedrock_reviewer_model_id`** (single ID — all three reviewer profiles use it when `revy_reviewer_provider=bedrock`).
- Optional: `revy_bedrock_inference_profile_arn` — documented in env example; code may ignore in v1 if unset.
- `bedrock_enabled()` — region + at least one Bedrock model id configured.
- Resolver: when `revy_judge_provider=bedrock` or `revy_reviewer_provider=bedrock`, return `ModelRef` with Bedrock model ids from env.
- `judge_llm_enabled()` / `reviewer_llm_enabled()` return true for Bedrock when `bedrock_enabled()` (not `anthropic_api_key`).
- Register Bedrock models in **`model_registry.py`** (same file as M0).
- Add `boto3` to Pipfile if absent.
- Default production unchanged: reviewer `moonshot`, judge `anthropic` unless env overrides.

## Out of scope for M1

- Workspace policy → **M2**
- UI / catalog API → **M2** / **M3**
- Per-profile Bedrock reviewer env vars (use workspace overrides in M2 instead)

---

## M1.1 — Config + registry entries

**What:** Bedrock settings fields; registry entries for configured Bedrock model ids; `bedrock_enabled`; env examples + `revy_bedrock_inference_profile_arn` comment.

**Files:** `backend/app/core/config.py`, `backend/app/constants/model_registry.py`, `backend/.env.example`, `deploy/env-examples/backend.env.production.example`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_model_policy.py -k bedrock_config -q` — green.

---

## M1.2 — Bedrock integration module

**What:** Async `complete_review` + `judge_finding` with explicit `model_id`, `region`; mocked boto3 in tests.

**Files:** `backend/app/integrations/bedrock_review.py`, `backend/tests/unit/test_bedrock_review.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_bedrock_review.py -q` — green.

---

## M1.3 — Resolver + dispatch Bedrock branch

**What:** Env branches for Bedrock judge/reviewer; dispatch routes to `bedrock_review`; enabled helpers cover Bedrock.

**Files:** `backend/app/services/model_policy.py`, `backend/app/integrations/llm_dispatch.py`, `backend/tests/unit/test_model_policy.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_model_policy.py -k bedrock -q` — green.

---

## M1.4 — Ops docs

**What:** Bedrock block in `docs/saas-base/OPS.md`, `docs/utils/GITHUB_APP_TARGET_CONFIG.md` — IAM role, region, inference profile note.

**Files:** `docs/saas-base/OPS.md`, `docs/utils/GITHUB_APP_TARGET_CONFIG.md`

**Deliverable:** Manual review — Bedrock env documented.

---

## M1.5 — Pipeline regression (Bedrock judge path)

**What:** `test_github_finding_judge.py` — judge runs when `revy_judge_provider=bedrock` and Bedrock mocked (no Anthropic key). `test_github_review.py` — optional Bedrock reviewer path.

**Files:** `backend/tests/unit/test_github_finding_judge.py`, `backend/tests/unit/test_github_review.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_review.py tests/unit/test_bedrock_review.py -q` — green.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint
pipenv run pytest tests/unit/test_model_policy.py tests/unit/test_bedrock_review.py tests/unit/test_github_finding_judge.py tests/unit/test_github_review.py tests/unit/test_moonshot_review.py tests/unit/test_anthropic_review.py -q
```

**Human gate (non-gate):** Staging — `REVY_JUDGE_PROVIDER=bedrock` + IAM; one judge call; check `judge_provider`/`judge_model_id` on outcome row.

**Deploy:** Env only; migration `0022` from M0 must already be applied.

**Next:** [`MODEL_POLICY_M2_EXECUTION.md`](./MODEL_POLICY_M2_EXECUTION.md)
