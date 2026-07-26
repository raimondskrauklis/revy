# docs/review-pipeline/waves/REVIEW_PIPELINE_R3_EXECUTION.md

# R3 — Indexing (execution)

Phase **R3** of [REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md](../REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md). **Depends on** R2 (`review-r2-v1`).

**GitHub App:** Contents Read (already in [GITHUB_APP_TARGET_CONFIG.md](../../utils/GITHUB_APP_TARGET_CONFIG.md)); tarball fetch via installation token.

**Goal:** Chunk and embed PR revision source; store pgvector rows; expose retrieval for R4.

**Authority:** `internal-docs/product/revy/docs/architecture.md`, `deploy/sql/postgres-extensions.sql` (`vector`).

## Decisions locked for R3

- **Tables:** `github_index_jobs` (per revision run), `github_code_chunks` (text + `vector(512)` embedding).
- **Embedding (v1 shipped):** Voyage API — `VOYAGE_API_KEY` required; model `voyage-3-lite`, dim **512** (`REVY_EMBEDDING_MODEL`, `REVY_EMBEDDING_DIMENSIONS`); disabled when key empty → `503 embeddings_disabled`.
- **Embedding (parallel track — architecture §11.3.1):** `REVY_EMBEDDING_BACKEND=voyage` (default) \| `local` when self-hosted backend ships; local candidates `jina-embeddings-v2-base-code` (CPU), `nomic-embed-code` (GPU); weights cache `REVY_HF_CACHE_PATH`. Eval upgrade for API path: `voyage-code-3` (Matryoshka dims; architecture default eval dim 1024).
- **Reranker (future retrieval stack §11.3):** parallel API (`voyage` rerank) vs local `bge-reranker-v2-m3` via `REVY_RERANKER_BACKEND` — not in R3 v1.
- **Source fetch:** GitHub tarball `GET /repos/{owner}/{repo}/tarball/{ref}` → extract under `REVY_WORKTREES_ROOT/{revision_id}`.
- **Chunking:** line-aware splits, max 2000 chars, skip binary paths + `node_modules`/`.git`/vendor dirs.
- **Trigger:** `POST …/pull-requests/{pr_id}/revisions/{revision_id}/index` (admin) → Celery `indexing` queue; **no** auto-index on `push` / `synchronize` ([Q11](../REVIEW_PIPELINE_FINDINGS.md) → R8 automation).
- **Retrieval:** `GET …/revisions/{revision_id}/chunks` list; service `search_revision_chunks(query, top_k)` for R4 (cosine via pgvector).
- **Out of scope (R3 v1 code):** symbol index, cross-repo search, auto-index on webhook, **local/HF embedding backend impl**, hybrid FTS+RRF rerank. Local/API-parallel embedding policy is **documented** in FINDINGS + `architecture.md` §11.3.1 for follow-up.

---

## R3.1 — Schema migration

**What:** Migration `0013_github_indexing`; `GitHubIndexJobORM`, `GitHubCodeChunkORM`; `GitHubIndexJobStatus` enum; pgvector column.

**Files:** `alembic/versions/…_github_indexing.py`, `models/github_index_job.py`, `models/github_code_chunk.py`, `constants/enums.py`

**Deliverable:** migration applies; `vector` extension assumed present.

---

## R3.2 — Chunking + tarball extract

**What:** `services/code_chunking.py` (pure); `integrations/github_archive.py` (tarball download + safe extract + file walk).

**Files:** `integrations/github_api.py` (tarball URL helper), tests

**Deliverable:** `pytest tests/unit/test_code_chunking.py tests/unit/test_github_archive.py -q` — green.

---

## R3.3 — Voyage embeddings client

**What:** `integrations/voyage_embeddings.py` — batch embed; `embeddings_enabled` on settings.

**Files:** `core/config.py`, `integrations/voyage_embeddings.py`, `tests/unit/test_voyage_embeddings.py`

**Deliverable:** unit tests with mocked httpx.

---

## R3.4 — Index service + index_tasks worker

**What:** `services/github_indexing.py` — create job, run pipeline, store chunks; `workers/index_tasks.py`; register in `celery_app.py`.

**Files:** `services/github_indexing.py`, `workers/index_tasks.py`, `tests/unit/test_github_indexing.py`, `tests/unit/test_index_tasks.py`

**Deliverable:** worker unit tests green.

---

## R3.5 — API + docs

**What:** Admin index trigger + member chunk list/search routes; update `GITHUB_WEBHOOK_DEV.md` / findings verification.

**Files:** `api/v1/workspaces/installation_indexing.py`, route tests, docs

**Deliverable:** phase gate green.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_code_chunking.py \
  tests/unit/test_github_archive.py \
  tests/unit/test_voyage_embeddings.py \
  tests/unit/test_github_indexing.py \
  tests/unit/test_index_tasks.py \
  tests/unit/test_github_index_routes.py \
  -q
```

**Deploy:** `alembic upgrade head`; set `VOYAGE_API_KEY`, `REVY_WORKTREES_ROOT`; worker consumes `indexing` queue.

**Human gate:** index one revision on staging; `github_code_chunks` rows with non-null embeddings.

**Next:** [REVIEW_PIPELINE_R4_EXECUTION.md](./REVIEW_PIPELINE_R4_EXECUTION.md).
