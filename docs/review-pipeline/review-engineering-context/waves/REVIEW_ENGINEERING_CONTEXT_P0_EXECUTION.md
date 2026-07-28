# Review engineering context P0 — Foundations (execution)

Phase **P0** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](../REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) RCX-G1, G9, G2b. **P0 only.**

**Goal:** SSOT schema, config caps (512 KB default), migration `0029`, retrieve-manifest + `context_stats` field contract (values empty until P2).

## Decisions locked for P0

- SSOT path: `.greptile/review-context.json` — shape: `active_program` (string) + `programs[]` with `id`, `scope` (globs), `paths[]` (`path`, `description`).
- Initial SSOT lists **review-engineering-context** program only (3 docs: execution, findings, general plan paths).
- `context_stats` JSONB nullable on `github_review_runs` — keys per general plan P0 (denormalized snapshot contract).
- Retrieve manifest adds keys with defaults: `engineering_context_injected=false`, `engineering_context_bytes=0`, `diff_max_bytes`, `unified_diff_bytes=0`, `active_program=null`, `lock_ids_extracted=[]`, `engineering_context_deduped_paths=[]` — populated in P2.
- Config env: `REVY_DIFF_MAX_BYTES` (default 524288), `REVY_ENGINEERING_CONTEXT_MAX_BYTES` (default 32768), `REVY_PR_BODY_MAX_BYTES` (default 4096).
- `github_review.py` still uses module constants in P0 — **wire config reads in P2**; P0 only adds settings + tests.

## PR review context (first commit)

- **Greptile:** add `review-engineering-context/**` to generated `files.json` in P3 — P0 adds SSOT only; optional minimal Greptile entry for program PR if needed for dogfood (paths under `docs/review-pipeline/review-engineering-context/**`, `scope: ["backend/**"]`).
- **Bugbot:** `.cursor/BUGBOT.md` — add RCX program links + active program line `review-engineering-context`.

## Out of scope for P0

- GitHub file fetch → **P1**
- Moonshot inject → **P2**
- `files.json` generator → **P3**
- Judge → **P4**

---

## P0.1 — Migration `0029_review_context_stats`

**What:** Hand-written Alembic revision — `context_stats JSONB NULL` on `github_review_runs`.

**Files:** `backend/alembic/versions/2026_07_29_1200_0029_review_context_stats.py`, `backend/app/models/github_review_run.py`

**Deliverable:**

```bash
cd backend && pipenv run alembic upgrade head
pipenv run pytest tests/unit/test_github_review_run_model.py -q
```

Create `test_github_review_run_model.py` asserting `context_stats` column on ORM if no existing test.

**LOOP pause:** operator runs migration on staging after merge.

---

## P0.2 — Config caps

**What:** Add settings to `config.py` + `.env.example`; unit test defaults (524288 / 32768 / 4096).

**Files:** `backend/app/core/config.py`, `backend/.env.example`, `backend/tests/unit/test_engineering_context_config.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_engineering_context_config.py -q
```

---

## P0.3 — `engineering_context` module + SSOT parser

**What:** Create `app/services/engineering_context/` — `manifest.py` (parse/validate SSOT JSON), `types.py` (`ReviewContextManifest`, `ProgramEntry`); load from bytes/string; validate active_program references a program id.

**Files:** `backend/app/services/engineering_context/__init__.py`, `manifest.py`, `types.py`, `backend/tests/unit/test_engineering_context_manifest.py`, `.greptile/review-context.json`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_engineering_context_manifest.py -q
python -m json.tool .greptile/review-context.json > /dev/null
```

---

## P0.4 — Retrieve manifest + `context_stats` contract

**What:** Add `engineering_context_manifest_defaults()` helper; merge into `build_retrieval_manifest` return dict; add `ContextStats` typed dict / pydantic model for `github_review_runs.context_stats` column; ORM field on `GitHubReviewRunORM`.

**Files:** `backend/app/services/github_review.py`, `backend/app/services/engineering_context/stats.py`, `backend/app/models/github_review_run.py`, `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k "retrieval_manifest or context_stats" -q
```

---

## P0.5 — Staging script + PR review context

**What:** Extend `judge_json_contract_staging_metrics.py` to aggregate `context_stats` from `github_review_runs` when column populated; add Greptile/Bugbot RCX wiring per PR review context above.

**Files:** `backend/scripts/judge_json_contract_staging_metrics.py`, `.greptile/files.json` (minimal RCX entry if not deferred to P3), `.cursor/BUGBOT.md`, `docs/utils/BACKEND_SCRIPTS_RUNBOOK.md`

**Deliverable:**

```bash
cd backend && pipenv run ruff check scripts/judge_json_contract_staging_metrics.py app/services/engineering_context/
python -m json.tool .greptile/review-context.json > /dev/null
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/services/engineering_context/ app/models/github_review_run.py app/core/config.py
pipenv run pytest tests/unit/test_engineering_context_manifest.py tests/unit/test_github_review.py -k "retrieval_manifest or context_stats" tests/unit/test_engineering_context_config.py tests/unit/test_github_review_run_model.py -q
```

**Deploy:** ship migration `0029` before P2 dogfood on staging.

**Next:** [REVIEW_ENGINEERING_CONTEXT_P1_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P1_EXECUTION.md)
