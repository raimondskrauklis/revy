# docs/review-pipeline/waves/REVIEW_PIPELINE_R4_EXECUTION.md

# R4 — Review run (execution)

Phase **R4** of [REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md](../REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md). **Depends on** R3 (`review-r3-v1`).

**Goal:** Run LLM review for a PR revision, persist structured findings, expose member read APIs.

**Authority:** `backend/app/core/config.py` (LLM + timeout env), [GITHUB_APP_TARGET_CONFIG.md](../../utils/GITHUB_APP_TARGET_CONFIG.md) § Model providers.

## Decisions locked for R4

- **Tables:** `github_review_runs` (per revision attempt), `github_findings` (structured rows per run).
- **Run status:** `pending` → `processing` → `completed` \| `failed` (`GitHubReviewRunStatus`).
- **Finding shape:** `severity` (`info` \| `warning` \| `error` \| `critical`), `category` (`security` \| `bug` \| `performance` \| `style` \| `maintainability` \| `other`), `title`, `message`, optional `file_path` + `start_line` + `end_line`. Schema includes `style` for forward compatibility; **R4-Q5** — prompt/parsing must drop style/lint findings (CI owns style); do not persist `category=style` rows in R4 v1.
- **Primary LLM (Moonshot Kimi):** `REVY_LLM_PROVIDER` = `moonshot` (default). OpenAI-compatible client at `https://api.moonshot.ai/v1`. `503 llm_disabled` when `MOONSHOT_API_KEY` missing.
- **Model tier by profile:** `standard` → `kimi-k2.7-code`; `deep` / `critical` → `kimi-k3` (override via `REVY_MOONSHOT_MODEL_STANDARD`, `REVY_MOONSHOT_MODEL_DEEP` — see `backend/.env.example`). Authority: `internal-docs/product/revy/docs/architecture.md` §13–14.
- **Anthropic:** **not** the R4 primary — reserved for R5 judge / cross-family escalation (`ANTHROPIC_API_KEY`, `judge` queue). Optional `anthropic_review.py` scaffold in R4.2 for adapter reuse only.
- **Profile → timeout:** `standard` / `deep` / `critical` map to existing `revy_revision_timeout_*_seconds` settings; Celery `soft_time_limit` = profile timeout, `time_limit` = timeout + 60s.
- **Prerequisite:** latest `github_index_jobs` for revision must be `completed` (else `409` + `error_code=index_required` via `ConflictError`); `embeddings_enabled` (`VOYAGE_API_KEY`) and `github_api_enabled` required for context retrieval.
- **Context:** R3 `search_revision_chunks` — queries from PR title + fixed lenses (`security vulnerabilities`, `logic bugs`, `performance issues`); merge top chunks (dedupe by `file_path`+`chunk_index`, cap 30).
- **Prompt output:** single JSON object `{"findings":[…]}`; invalid JSON → run `failed` with stored error.
- **Trigger:** `POST …/pull-requests/{pr_id}/revisions/{revision_id}/review` (`admin_users`, same as R3 index) → Celery `review` queue; `idempotency_guard` on trigger; **no** auto-review on `push`.
- **Concurrency:** reject new trigger with `409` + `error_code=review_in_progress` when a run for the revision is `pending` or `processing`.
- **Audit:** `record_audit` on review trigger (`review.run_requested`).
- **Out of scope:** judge/reconcile (R5), GitHub publish (R6), plan-gated volume (Q9), auto-review on webhook, multi-model ensemble.

---

## R4.1 — Schema migration

**What:** Migration `0014_github_review_runs`; `GitHubReviewRunORM`, `GitHubFindingORM`; enums `GitHubReviewRunStatus`, `FindingSeverity`, `FindingCategory`, `ReviewProfile`.

**Files:** `alembic/versions/…_github_review_runs.py`, `models/github_review_run.py`, `models/github_finding.py`, `constants/enums.py`, `models/__init__.py`

**Deliverable:** migration applies; FKs to `github_pull_request_revisions`, `workspaces`.

**LOOP pause:** hand-written Alembic revision — human runs `alembic upgrade head` on deploy.

---

## R4.2 — LLM provider clients

**What:** `integrations/anthropic_review.py` (messages API, structured JSON); `integrations/moonshot_review.py` (OpenAI client); add `settings.llm_enabled` + `settings.revy_revision_timeout_seconds(profile)` mapping `revy_revision_timeout_*_seconds` env vars.

**Files:** `core/config.py`, `integrations/anthropic_review.py`, `integrations/moonshot_review.py`, `tests/unit/test_anthropic_review.py`, `tests/unit/test_moonshot_review.py`

**Deliverable:** `pytest tests/unit/test_anthropic_review.py tests/unit/test_moonshot_review.py -q` — green with mocked httpx/OpenAI.

---

## R4.3 — Review pipeline service

**What:** `services/github_review.py` — create run, build context via R3 search, call LLM, parse findings, persist rows; profile + provider selection.

**Files:** `services/github_review.py`, `schemas/github_review.py`, `tests/unit/test_github_review.py`

**Deliverable:** unit tests cover happy path, missing index (`409` / `index_required`), invalid LLM JSON (`failed` run).

---

## R4.4 — Review worker

**What:** `workers/review_tasks.py` — `review_pull_request_revision(review_run_id)`; register import in `celery_app.py` (route already `review` queue). **Do not** enqueue R5 reconcile here — R5.3 adds hook after `review-r4-v1`.

**Files:** `workers/review_tasks.py`, `tests/unit/test_review_tasks.py`

**Deliverable:** worker unit tests green; retry policy matches index_tasks pattern.

---

## R4.5 — API + docs

**What:** Admin review trigger + member read routes (`GET …/review-run`, `GET …/findings`); audit on trigger; update `GITHUB_WEBHOOK_DEV.md` § review verification.

**Files:** `api/v1/workspaces/installation_review.py`, `api/v1/workspaces/__init__.py`, route tests, docs

**Deliverable:** phase gate green.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_anthropic_review.py \
  tests/unit/test_moonshot_review.py \
  tests/unit/test_github_review.py \
  tests/unit/test_review_tasks.py \
  tests/unit/test_github_review_routes.py \
  -q
```

**Deploy:** `alembic upgrade head` (through `0014`); set `VOYAGE_API_KEY`, `MOONSHOT_API_KEY`; worker consumes full Revy queue list per [PROGRAM](../REVIEW_PIPELINE_PROGRAM.md) §5.

**Human gate:** index one revision (R3), trigger review, confirm `github_findings` rows and API list returns them.

**Status:** Implemented — PR [#24](https://github.com/raimondskrauklis/revy/pull/24).

**Next:** [REVIEW_PIPELINE_R5_EXECUTION.md](./REVIEW_PIPELINE_R5_EXECUTION.md) (PR [#25](https://github.com/raimondskrauklis/revy/pull/25)).
