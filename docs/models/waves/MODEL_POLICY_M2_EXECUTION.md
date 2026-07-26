# docs/models/waves/MODEL_POLICY_M2_EXECUTION.md

# M2 — Workspace model policy API (execution)

Phase **M2** of [`MODEL_POLICY_GENERAL_PLAN.md`](../MODEL_POLICY_GENERAL_PLAN.md). **M2 only.**

**Goal:** Per-workspace overrides in `workspace_model_policies`; resolver reads DB; admin API + catalog.

**Depends on:** M1 PASS.

## Decisions locked for M2

- Table **`workspace_model_policies`**: `workspace_id`, `role`, `provider`, `model_id`, `region` nullable; unique `(workspace_id, role)`.
- **Override semantics:** no row → platform env default; PATCH with `null` for a role **deletes** row (no `use_platform_default` column).
- GET returns `{ overrides: {...}, effective: {...} }` — effective from `resolve_model` per role.
- Roles: `reviewer_standard`, `reviewer_deep`, `reviewer_critical`, `judge` — not `embedding`.
- Catalog: `build_model_catalog()` imports **`model_registry.py`** + filters by `reviewer_llm_enabled` / `judge_llm_enabled` / provider credentials.
- Anthropic/Bedrock: same catalog entry may appear for multiple reviewer roles; workspace may set **distinct** overrides per role.
- `async resolve_model(session, …)` loads override row when present; validates against catalog.
- Permission: `admin:users` (v1).
- Audit: `workspace.model_policy_updated`.
- Migration **`0023_workspace_model_policies`** (head after `0022`).

## Out of scope for M2

- Frontend → **M3**
- Jury, embedding role, BYOK

---

## M2.1 — Schema migration

**What:** `0023_workspace_model_policies`; `WorkspaceModelPolicyORM`.

**Files:** `backend/alembic/versions/…_0023_workspace_model_policies.py`, `backend/app/models/workspace_model_policy.py`, `backend/app/models/__init__.py`

**Deliverable:** `cd backend && pipenv run alembic upgrade head` — applies after `0022`.

**LOOP pause:** after migration commit.

---

## M2.2 — Catalog service

**What:** `build_model_catalog()` from shared registry; group by role eligibility; unit tests.

**Files:** `backend/app/services/model_catalog.py`, `backend/app/schemas/model_policy.py`, `backend/tests/unit/test_model_catalog.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_model_catalog.py -q` — green.

---

## M2.3 — Resolver workspace branch

**What:** `resolve_model` SELECT override by `(workspace_id, role)`; fallback to env; tests for override, delete, invalid catalog rejection.

**Files:** `backend/app/services/model_policy.py`, `backend/app/services/workspace_model_policy.py`, `backend/tests/unit/test_model_policy.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_model_policy.py -k workspace -q` — green.

---

## M2.4 — API routes + audit

**What:** `GET/PATCH …/model-policy`, `GET …/model-catalog`; admin gate; audit on PATCH.

**Files:** `backend/app/api/v1/workspaces/model_policy.py`, `backend/tests/unit/test_workspace_model_policy_routes.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_workspace_model_policy_routes.py -q` — green.

---

## M2.5 — Pipeline integration tests

**What:** Workspace Bedrock judge override → `judge_model_id` on outcome matches override; review run `model_id` matches workspace reviewer override.

**Files:** `backend/tests/unit/test_github_finding_judge.py`, `backend/tests/unit/test_github_review.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_github_review.py tests/unit/test_workspace_model_policy_routes.py tests/unit/test_model_catalog.py -q` — green.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint
pipenv run alembic upgrade head
pipenv run pytest tests/unit/test_model_policy.py tests/unit/test_model_catalog.py tests/unit/test_workspace_model_policy_routes.py tests/unit/test_github_finding_judge.py tests/unit/test_github_review.py -q
```

**Deploy:** `alembic upgrade head` through `0023`.

**Next:** [`MODEL_POLICY_M3_EXECUTION.md`](./MODEL_POLICY_M3_EXECUTION.md)
