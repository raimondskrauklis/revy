# Review pipeline R3 — Indexing

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** workspace tenancy; installation token for Contents read; unit tests; hand-written Alembic; `REVY_REPOS_ROOT` / worktree paths from config.

**Authority:** [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) § R3, `internal-docs/product/revy/docs/architecture.md`, deploy SQL (`vector` extension).

---

## Goal

Chunk and embed repository content at a given revision so the R4 review stage has retrievable context (not full-repo mirror in Postgres).

**Scope:** In — `index_tasks` on `indexing` queue; shallow clone or worktree per repo revision; chunking strategy; embedding via `VOYAGE_API_KEY` (or configured backend); pgvector storage; index job status per PR revision; retrieval API for review worker. Out — symbol/AST index; cross-repo search; incremental index on every `push` (defer until R4 needs it).

**Deliverables:** Embeddings rows + vector index; job record linked to `github_pull_request_revisions`; failed jobs retry + auditable status; env docs for `REVY_REPOS_ROOT`, `REVY_WORKTREES_ROOT`, `REVY_HF_CACHE_PATH`.

**Depends on:** R2 (PR + revision entities exist).

**Status:** Shipped — tag `review-r3-v1`.

**Next:** `create-execution-plan` when R2 ships — [waves/REVIEW_PIPELINE_R3_EXECUTION.md](./waves/REVIEW_PIPELINE_R3_EXECUTION.md) (to be created).

**Next phase:** [REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md](./REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md).
