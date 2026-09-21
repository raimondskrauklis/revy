# docs/free-plan-credits/FREE_PLAN_CREDITS_P0_EXECUTION.md

# P0 — Schema + open the gate (execution)

Phase **P0** of [`FREE_PLAN_CREDITS_GENERAL_PLAN.md`](./FREE_PLAN_CREDITS_GENERAL_PLAN.md). Baseline: [`FREE_PLAN_CREDITS_FINDINGS.md`](./FREE_PLAN_CREDITS_FINDINGS.md) §Track 1, §Track 3. **P0 only.**

**Goal:** Allow any workspace to install GitHub; add `completed_review_runs` + `review_run_limit` columns to `workspaces`; backfill existing workspaces; remove all `installations.create` plan gates.

## Decisions locked for P0
- `completed_review_runs` INT NOT NULL DEFAULT 0, `review_run_limit` INT NULL (NULL = unlimited = Pro)
- Backfill: free/NULL → 25, pro → NULL
- Remove gate from 5 locations: `PLAN_FEATURES` dict + 3 endpoint guards + 1 service-layer guard
- New workspaces get `review_run_limit = 25` in `onboarding.py:activate_user_with_workspace()`
- Migration number: `0036` (chained after `0035_finding_group_claim_slot`)

## PR review context (required when code + docs ship in one PR)
- **SSOT (Moonshot inject):** `.revy/review-context.json` — set `active_program: "free-plan-credits"`; `programs[]` = one entry only; `scope: "backend` + `docs/free-plan-credits/FREE_PLAN_CREDITS_P0_EXECUTION.md`, `docs/free-plan-credits/FREE_PLAN_CREDITS_FINDINGS.md`, `docs/free-plan-credits/FREE_PLAN_CREDITS_GENERAL_PLAN.md"`
- **Bugbot:** `.cursor/BUGBOT.md` — active program: `free-plan-credits`; links to same three docs
- **Agent mirror:** copy SSOT to `.agent/review-context.json`
- **Ship in P0 commit.**

## Out of scope for P0 (later phases)
- Credit check in `create_review_run()` → **P1**
- Atomic increment in `run_review_run()` → **P1**
- `ForbiddenError` catch in autostart pipeline → **P1**
- Stripe downgrade/upgrade credit mutation → **P1**
- Me endpoint credit fields → **P2**
- PlanSummaryWidget counter → **P2**
- ReviewTriggerBar credit gate → **P2**

---

## P0.0 — Program PR review context (SSOT + Bugbot)

**What:** Wire SSOT (`programs[]`, `scope`) + Bugbot context for this program.

**Files:** `.revy/review-context.json`, `.cursor/BUGBOT.md`, `.agent/review-context.json`

**Deliverable:** `pipenv run pytest tests/unit/test_engineering_context_manifest.py`

---

## P0.1 — Alembic migration (hand-written)

**What:** Add `completed_review_runs` and `review_run_limit` columns to `workspaces`; backfill existing workspaces.

**Files:**
- `backend/alembic/versions/2026_09_21_0900_0036_workspace_credit_limits.py` (new — hand-written, no --autogenerate)
- DDL: `ALTER TABLE workspaces ADD COLUMN completed_review_runs INTEGER NOT NULL DEFAULT 0, ADD COLUMN review_run_limit INTEGER NULL`
- Backfill: `UPDATE workspaces SET review_run_limit = 25 WHERE plan IS NULL OR plan = 'free'; UPDATE workspaces SET review_run_limit = NULL WHERE plan = 'pro'`

**Deliverable:** `pipenv run alembic upgrade head` succeeds. Verify columns exist: `SELECT column_name FROM information_schema.columns WHERE table_name = 'workspaces' AND column_name IN ('completed_review_runs', 'review_run_limit')`.

> ⚠️ **LOOP pause after this subphase** — hand-written migration. Agent stops; user verifies DDL on staging before continuing.

---

## P0.2 — Update WorkspaceORM model

**What:** Add `completed_review_runs` and `review_run_limit` mapped columns to `WorkspaceORM`.

**Files:** `backend/app/models/workspaces.py`

**Deliverable:** `pipenv run pytest tests/unit/test_workspace_credit_model.py` — validates `completed_review_runs` defaults to 0, `review_run_limit` nullable, server defaults correct.

---

## P0.3 — Set default on new workspace creation

**What:** In `activate_user_with_workspace()`, set `review_run_limit = 25` on the new `WorkspaceORM`. Both registration and auto-provision flows go through this.

**Files:** `backend/app/services/onboarding.py` — line 52: `WorkspaceORM(slug=slug, name=name)` → add `review_run_limit=25`

**Deliverable:** `pipenv run pytest tests/unit/test_onboarding_credit_default.py` — new workspace has `review_run_limit = 25`.

---

## P0.4 — Remove `installations.create` gate (5 locations)

**What:** Remove the only plan gate blocking free-plan users from installing GitHub.

**Files:**
1. `backend/app/core/plan_gates.py:21` — drop `"installations.create": "pro"` from `PLAN_FEATURES` dict (leave empty dict)
2. `backend/app/api/v1/workspaces/installations.py:64` — remove `_: Annotated[None, Depends(require_plan_feature("installations.create"))] = None,` from `post_workspace_installation`
3. `installations.py:91` — remove from `post_workspace_installation_connect`
4. `installations.py:122` — remove from `post_workspace_installation_verify`
5. `backend/app/services/github_installations.py:142-148` — remove the `workspace_has_feature(workspace, "installations.create")` guard block from `bind_github_installation` (5 lines)

**Deliverable:** `pipenv run pytest tests/unit/test_installations_no_plan_gate.py` — installation endpoints return 201/200 without plan gate error. `plan_upgrade_required` error code stays in exceptions (harmless dead code).

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_engineering_context_manifest.py tests/unit/test_workspace_credit_model.py tests/unit/test_onboarding_credit_default.py tests/unit/test_installations_no_plan_gate.py
```

**Human gate:** Review migration `0036` DDL + backfill SQL; run `alembic upgrade head` on staging.

**Deploy:** Can ship standalone — no coupling. Gate removal is safe (no other code depends on `installations.create` gate).

**Next:** [`FREE_PLAN_CREDITS_P1_EXECUTION.md`](./FREE_PLAN_CREDITS_P1_EXECUTION.md)