# Review quality R2 — Incremental index (C1 copy-forward)

General plan from [REVIEW_QUALITY_FINDINGS.md](./REVIEW_QUALITY_FINDINGS.md) tracks **I + C1**. **No execution steps.** Same PR as R1 (S1).

**Cross-cutting:** workspace tenancy; extend pipeline trace `index` step manifest; hand-written Alembic; unit tests.

**Depends on:** R1 slice in same branch — `base_sha`, compare API, `index_mode`, changed-file detection, D13 tarball filter.

---

## Goal

On `pull_request.synchronize`, **copy-forward** unchanged chunks and re-embed **delta only** (C1) — diff-mode reviews stay fast and cheap on every push.

---

## Scope

**In:**

| Piece | Behavior |
|-------|----------|
| **C1 copy-forward** | Clone rows where `(file_path, chunk_index, content_hash)` matches parent revision → new `revision_id`, reuse embedding |
| **content_hash** | On `github_code_chunks` (I1) |
| **Delta embed** | Chunk + Voyage only for changed/new paths from compare |
| **Deletes** | Remove chunks for paths dropped from compare vs parent |
| **Job mode** | `incremental` vs `full` re-embed flag on index job (I3) |
| **Manifest** | `reused_count`, `new_count`, `embed_batches`, `index_mode` in pipeline trace |

**Out:** LSP / symbol hop; cross-repo index; changing D13 compare-first strategy.

**Note:** D10 fingerprint ships in R1 slice; R2 does not duplicate.

**First push:** No parent revision — copy-forward is a no-op; embed all changed paths from compare.

**Deletes:** Compare parent revision’s indexed paths vs current compare — remove chunks for paths dropped.

---

## Deliverables

1. Second push on same PR embeds **far fewer** Voyage batches than first (staging metric).
2. Unchanged files reuse parent embeddings without Voyage call.
3. Index job manifest records incremental stats.
4. `index_mode=full` still works; copy-forward applies to full-scoped jobs on synchronize.
5. Unit tests: hash match → reuse; content change → re-embed; deleted file → chunk removed.

---

## Depends on

R1 compare + `index_mode=diff` + pipeline trace (same PR).

---

## Next

Section in `waves/REVIEW_QUALITY_EXECUTION.md`.
