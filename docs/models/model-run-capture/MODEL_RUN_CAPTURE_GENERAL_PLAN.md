# Model run capture — general plan

**Baseline:** [MODEL_RUN_CAPTURE_FINDINGS.md](./MODEL_RUN_CAPTURE_FINDINGS.md) (2026-08-10, post arch peer-review pass 1)  
**Sibling:** [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](../../review-pipeline/pipeline-observability/PIPELINE_OBSERVABILITY_GENERAL_PLAN.md) — share `github_llm_call_attempts`; MRC adds model identity surfaces PO does not own.

**Thesis:** Every pipeline run records **which models executed** at each stage — embeddings first (staging on `voyage-code-3.5`), then reviewer/judge/publish — queryable in DB and staging metrics after env or workspace policy changes.

**Locked:** MRC-Q1–Q6, MRC-Q8–Q10 per findings.

**Wave order:** Coordinate with pipeline observability — **PO-P1.4 ships Voyage recorder**; MRC-P1 verifies `request_model` and fills judge/publish step gaps in same wave or immediately after.

---

## Cross-cutting (every phase)

- **Execution-time values only** — capture model at HTTP/call site (`github_indexing`, integrations), persist through manifest/steps/attempts; never re-read `settings` in trace writers.
- **Tests:** unit coverage for manifest fields, attempt `request_model`, snapshot population, `embed_batches=0` null semantics.
- **Migrations:** hand-written Alembic when adding columns; manifest JSONB keys need no migration.
- **i18n:** operator-facing API labels only if UI ships in MRC-P3; no user PR UI in v1.
- **Lineage:** `models_snapshot` + pipeline manifest are the explainability surface for "what model reviewed this PR?"

---

## MRC-P0 — Index embedding identity (manifest + step)

**Goal:** Every pipeline-triggered index records Voyage model + dimensions on the index step artifact when embed HTTP actually runs.

**Scope — in:** Extend `_set_index_manifest_stats` in `github_indexing` to capture `embedding_provider`, `embedding_model`, `embedding_dimensions` at embed batch time; `record_index_pipeline_step` copies from job stats to manifest and sets index step `model_provider`/`model_id` on **both** create and update paths (including pre-existing `pending` step from `stash_pipeline_github_check_run_id`); when `embed_batches=0`, omit `embedding_*` or set null + `embedding_skipped_reason=reused_chunks_only` (MRC-Q8).

**Scope — out:** `github_llm_call_attempts`; chunk table column; manual-index jobs without pipeline run.

**Deliverables:** Next index job with embed HTTP on staging manifest shows `voyage-code-3.5` @ 1024; reuse-only index has no false model imputation.

**Depends on:** None.

---

## MRC-P1 — LLM attempt rows + judge/publish step models

**Goal:** All pipeline stages expose `provider` + `model_id` on steps and attempt rows where LLM HTTP runs.

**Scope — in:** **PO-P1.4 owns** Voyage `index_embed` attempt wiring — MRC verifies `request_model` matches manifest; add judge step `model_provider`/`model_id` in `record_judge_pipeline_step` (from resolved `ModelRef`); add publish step model fields when PO-P1 publish instrumentation lands; confirm review attempts already write `request_model`.

**Scope — out:** Token population beyond PO-P1; manual-index embeds (MRC-Q6).

**Deliverables:** Dogfood pipeline run has `index_embed` attempts with `request_model=voyage-code-3.5`; judge step row shows judge model.

**Depends on:** MRC-P0; [PO-P0](../../review-pipeline/pipeline-observability/PIPELINE_OBSERVABILITY_GENERAL_PLAN.md) (shipped); coordinate [PO-P1](../../review-pipeline/pipeline-observability/PIPELINE_OBSERVABILITY_GENERAL_PLAN.md) / PO-P1.4 for Voyage + publish paths.

---

## MRC-P2 — Pipeline models snapshot + staging metrics

**Goal:** One JSONB field per pipeline run summarizes all four roles; operator script groups by model and stage.

**Scope — in:** `github_pipeline_runs.models_snapshot` (migration); **terminal populate** after publish complete or pipeline failure hook (MRC-Q9) — rollup from index/review/**judge**/publish steps + attempts (judge runs in `reconcile_tasks` after review, before publish); extend `pipeline_observability_staging_metrics.py` with `GROUP BY step_type, provider, request_model`; optional retrieve manifest `query_embedding_model` (MRC-Q7, v1.1).

**Scope — out:** Cost rollup by model (PO-P3); cross-model mismatch alerts.

**Deliverables:** SQL/script answers "how many runs used voyage-code-3.5 vs voyage-code-3 since deploy?" broken down by `step_type`.

**Depends on:** MRC-P1.

---

## MRC-P3 — API exposure + staging sign-off

**Goal:** Pipeline trace API returns model identity for operators without raw SQL.

**Scope — in:** Extend pipeline run response with `models_snapshot`; flatten index manifest `embedding_*` keys on step/trace schema (manifest artifact parsing); staging validation memo row for embedding model capture.

**Scope — out:** Workspace settings UI; Sentry/OTel export (PO-P5).

**Deliverables:** API consumer sees embedding + reviewer + judge + publish models on completed dogfood run.

**Depends on:** MRC-P2.

---

## Next step

**Program code complete** — MRC-P0–P3 shipped ([#96](https://github.com/raimondskrauklis/revy/pull/96), [#98](https://github.com/raimondskrauklis/revy/pull/98), [#99](https://github.com/raimondskrauklis/revy/pull/99)).

**Operator:** staging sign-off complete — see [MODEL_RUN_CAPTURE_STAGING_VALIDATION.md](./MODEL_RUN_CAPTURE_STAGING_VALIDATION.md).
