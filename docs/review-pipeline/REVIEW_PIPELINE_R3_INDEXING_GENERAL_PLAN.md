# Review pipeline R3 — Indexing

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** workspace tenancy; installation token for Contents read; unit tests; hand-written Alembic; `REVY_REPOS_ROOT` / worktree paths from config.

**Authority:** [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) § R3, `internal-docs/product/revy/docs/architecture.md`, deploy SQL (`vector` extension).

---

## Goal

Chunk and embed repository content at a given revision so the R4 review stage has retrievable context (not full-repo mirror in Postgres).

**Scope:** In — `index_tasks` on `indexing` queue; tarball extract to worktree per revision (shipped — not git shallow clone); chunking strategy; **Voyage API embeddings** (v1 shipped backend); pgvector storage; index job status per PR revision; retrieval API for review worker. **Parallel track (documented, not R3 v1 code):** pluggable `EmbeddingBackend` for self-hosted models (`jina-embeddings-v2-base-code`, `nomic-embed-code`) via `REVY_HF_CACHE_PATH` — see `architecture.md` §11.3.1. Out — symbol/AST index; cross-repo search; auto-index on `push` / `synchronize` (deferred — [Q11](./REVIEW_PIPELINE_FINDINGS.md) → R8 automation); hybrid FTS+RRF rerank stack (architecture §11.3 stages 2–3 — post-R3 eval).

**Embedding policy:** **Voyage API** (`VOYAGE_API_KEY`, default `voyage-code-3` / dim **1024**; migration `0021` widens `github_code_chunks.embedding` from R3 v1 `vector(512)`). Matryoshka models pass `output_dimension` via `REVY_EMBEDDING_DIMENSIONS`. **Parallel track:** pluggable `EmbeddingBackend` for self-hosted models — same chunk schema, `REVY_EMBEDDING_BACKEND=local` when implemented.

**Deliverables:** Embeddings rows + vector index; job record linked to `github_pull_request_revisions`; failed jobs retry + auditable status; env docs for `REVY_REPOS_ROOT`, `REVY_WORKTREES_ROOT`, `VOYAGE_API_KEY`, `REVY_EMBEDDING_*`, `REVY_HF_CACHE_PATH`.

**Depends on:** R2 (PR + revision entities exist).

**Status:** Shipped — tag `review-r3-v1`.

**Next phase:** [REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md](./REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md).
