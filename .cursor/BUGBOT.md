# Bugbot — review-quality dogfood

When reviewing **backend** changes on `feat/review-quality`, treat these docs as the authoritative contract (not generic advice):

- [REVIEW_QUALITY_EXECUTION.md](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) — active RQ phase, locked schema, routes, gates
- [REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md) — locked Q# and storage model

**Active phase:** RQ4 (incremental copy-forward — content_hash, index_incremental, manifest stats).

**Check especially:**

- `github_indexing.py` — copy-forward from parent revision; `content_hash` on insert; `index_incremental=false` skips reuse
- Parent revision = prior row on same PR; first push is no-op copy-forward
- Index manifest: `reused_count`, `new_count`, `embed_batches` in pipeline index step
- Deleted paths vs parent file set removed on synchronize
