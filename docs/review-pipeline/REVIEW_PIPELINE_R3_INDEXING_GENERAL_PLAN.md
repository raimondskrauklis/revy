# Review pipeline R3 — Indexing

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** workspace tenancy; installation token for Contents read; unit tests; hand-written Alembic; `REVY_REPOS_ROOT` / worktree paths from config.

**Authority:** [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) § R3, `internal-docs/product/revy/docs/architecture.md`, deploy SQL (`vector` extension).

---

## Goal

Chunk and embed repository content at a given revision so the R4 review stage has retrievable context (not full-repo mirror in Postgres).

**Scope:** In — `index_tasks` on `indexing` queue; shallow clone or worktree per repo revision; chunking strategy; **Voyage API embeddings** (v1 shipped backend); pgvector storage; index job status per PR revision; retrieval API for review worker. **Parallel track (documented, not R3 v1 code):** pluggable `EmbeddingBackend` for self-hosted models (`jina-embeddings-v2-base-code`, `nomic-embed-code`) via `REVY_HF_CACHE_PATH` — see `architecture.md` §11.3.1. Out — symbol/AST index; cross-repo search; incremental index on every `push` (defer until R4 needs it); hybrid FTS+RRF rerank stack (architecture §11.3 stages 2–3 — post-R3 eval).

**Embedding policy:** **Start with API** (`VOYAGE_API_KEY`, default model `voyage-3-lite` / dim 512 in shipped code; eval upgrade path to `voyage-code-3` per architecture). **Keep local model path in parallel** for experiments and air-gapped deploys — same chunk schema, backend selected by `REVY_EMBEDDING_BACKEND` when implemented.

**Deliverables:** Embeddings rows + vector index; job record linked to `github_pull_request_revisions`; failed jobs retry + auditable status; env docs for `REVY_REPOS_ROOT`, `REVY_WORKTREES_ROOT`, `VOYAGE_API_KEY`, `REVY_EMBEDDING_*`, `REVY_HF_CACHE_PATH`.

**Depends on:** R2 (PR + revision entities exist).

**Status:** Shipped — tag `review-r3-v1`.

**Next phase:** [REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md](./REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md).
