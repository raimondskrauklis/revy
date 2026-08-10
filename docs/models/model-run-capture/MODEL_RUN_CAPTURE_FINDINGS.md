# Model run capture — findings

Baseline for **durable per-run model identity** across the Revy review pipeline — embeddings (Voyage), reviewer (Moonshot/Bedrock), judge (Anthropic/Bedrock), publish formatter — so operator metrics and forensics survive env and workspace policy changes (e.g. `voyage-code-3` → `voyage-code-3.5`, Kimi profile swaps).

**Date:** 2026-08-10 · **Status:** baseline-ready (architecture peer-review pass 1 incorporated)

**Evidence:** Code on `main`; staging operator switched `REVY_EMBEDDING_MODEL=voyage-code-3.5` (2026-08-10).

---

## Build principles

1. **Capture at execution time** — store the resolved `provider` + `model_id` used for that run, not today's env default.
2. **No imputation** — if a stage did not run or model unknown, field is `null`; never backfill from current settings.
3. **DB is SSOT for staging sign-off** — Voyage dashboard spend is vendor-side only; Revy must answer "what model indexed PR #N?"
4. **Align with pipeline observability** — model identity complements [PIPELINE_OBSERVABILITY_FINDINGS.md](../../review-pipeline/pipeline-observability/PIPELINE_OBSERVABILITY_FINDINGS.md) (tokens, `failure_class`, commits); do not fork attempt-row schema.
5. **Forward-only embedding upgrades OK** — operator does not require re-index of past PRs; per-revision capture still matters for any revision that is re-reviewed.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Model ref** | `(provider, model_id)` — e.g. `(voyage, voyage-code-3.5)`, `(moonshot, kimi-k2.7-code)` |
| **Pipeline role** | `embedding` · `reviewer` · `judge` · `publish` — maps to pipeline steps / attempt `step_type` |
| **Request model** | Model id sent to provider API (`request_model` on attempt rows) |
| **Models snapshot** | Per-`github_pipeline_runs` JSONB summary of models used across stages |

---

## What exists vs genuinely new (verified 2026-08-10)

### Captured today

| Role | Where | Verified |
|------|-------|----------|
| **Reviewer** | `github_review_runs.provider`, `model_id` | Set after `resolve_model` in `github_review.py` before LLM call |
| **Reviewer** | `github_pipeline_steps` (`review`) | `model_provider`, `model_id` from review run in `record_review_pipeline_step` |
| **Reviewer** | `github_llm_call_attempts` | `start_attempt` wired in `github_review.py` — `request_model=model_ref.model_id` when `pipeline_run` present |
| **Judge** | `github_finding_judge_outcomes.judge_model_id` | Per candidate outcome |
| **Judge** | `github_pipeline_steps` (`judge`) | **No** `model_provider`/`model_id` on step row today — only token totals (`record_judge_pipeline_step`) |
| **Publish** | `github_pipeline_steps` (`publish`) | **No** `model_provider`/`model_id` on step row today |
| **Embedding** | App logs only | `voyage_embeddings_request_failed` / rate-limit logs include `model` in `extra` — **not queryable** |

### Not captured (gaps)

| Gap | Impact | Severity |
|-----|--------|----------|
| **Index / embedding model** not on pipeline manifest or index step | Cannot tell if revision used `voyage-code-3` vs `voyage-code-3.5` after env change | **critical** |
| **Voyage embed attempts** not written to `github_llm_call_attempts` | No per-batch audit; **PO-P0 shipped** (table + recorder); **PO-P1.4 / Voyage wiring not shipped** | **high** |
| **Judge** step row missing `model_id` | Pipeline trace shows judge tokens but not which model | **medium** |
| **Retrieve-time query embed** model not recorded | Search uses current env model against stored chunk vectors — mismatch invisible | **high** |
| **Publish** formatter model not on pipeline step / attempts | Publish Moonshot model not durable if env changes mid-deploy | **medium** |
| **No pipeline-run models snapshot** | Operator must join steps + attempts + review_run to reconstruct | **medium** |
| **Staging metrics** no `GROUP BY request_model` | Cannot validate embedding switch in DB | **medium** |
| **`github_code_chunks` no `embedding_model`** | Vectors alone do not record which model produced them | **low** (defer — per-revision manifest sufficient v1) |
| **Workspace policy override** not denormalized | Run shows resolved model but not "workspace override vs platform default" | **low** (defer) |

### Reuse traps

| Trap | Detail |
|------|--------|
| **Env ≠ history** | `REVY_EMBEDDING_MODEL` on staging now `voyage-code-3.5`; old pipeline manifests lack model field entirely |
| **PO program overlap** | `github_llm_call_attempts` + `request_model` already designed in pipeline observability — extend, don't duplicate table |
| **`index_manifest_stats` ephemeral** | Set on job object in memory during `github_indexing`; only `embed_batches` copied to manifest — no model fields; must extend at embed time |
| **Index step may pre-exist `pending`** | `stash_pipeline_github_check_run_id` creates index step before embed — MRC-P0 must update model fields on existing step, not only `_create_completed_step` |
| **Review `model_id` only after retrieve** | Failed runs before resolve may have null `model_id` — acceptable; attempt rows should still capture intent when call starts |
| **Manual index jobs** | No `pipeline_run_id` — embed attempt rows skipped per PO-Q16; manifest-only capture optional |

---

## Target catalog (v1)

| Stage | Persist | Fields |
|-------|---------|--------|
| **Index embed** | Index step manifest + step `model_provider`/`model_id` | `embedding_provider`, `embedding_model`, `embedding_dimensions` — captured in **`github_indexing` at embed HTTP time**, copied to manifest (not re-read from `settings` in trace writer) |
| **Index embed HTTP** | `github_llm_call_attempts` | `step_type=index_embed`, `operation_name=embeddings`, `request_model`, `batch_size`, `index_job_id` — **owner: PO-P1.4**; MRC verifies `request_model` |
| **Retrieve query embed** | Retrieve step manifest (optional v1.1) | `query_embedding_model` when supplemental search runs |
| **Review** | Existing paths + ensure attempt rows on all success paths | `review_runs.model_id`, attempts `request_model` |
| **Judge** | Outcomes + step + attempts (MRC-P1) | `judge_model_id` on outcomes; add `model_provider`/`model_id` on judge **step** row; attempt rows per candidate |
| **Publish** | Pipeline step + attempts | `step_type=publish`, `request_model` |
| **Pipeline run rollup** | `github_pipeline_runs.models_snapshot` JSONB | `{ "embedding", "reviewer", "judge", "publish" }` — **single terminal write after publish** (or last terminal stage on failure); partial stages use whatever completed |

**Out of v1:** per-chunk `embedding_model` column; workspace-policy provenance; vendor billing reconcile.

---

## External context

| Topic | Relevance |
|-------|-----------|
| [voyage-embeddings findings](../voyage-embeddings/VOYAGE_CODE_4_FINDINGS.md) | Staging on `voyage-code-3.5`; forward-only — **must capture model per index job** |
| [MODEL_POLICY_FINDINGS.md](../MODEL_POLICY_FINDINGS.md) | Workspace overrides for reviewer/judge; execution-time resolve already returns `ModelRef` |
| [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](../../review-pipeline/pipeline-observability/PIPELINE_OBSERVABILITY_GENERAL_PLAN.md) | P1 ships Voyage attempt rows — **MRC-P1 aligns with PO-P1.4** |

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| MRC-Q1 | Folder | **locked** | `docs/models/model-run-capture/` |
| MRC-Q2 | Embedding model on chunk row vs manifest? | **locked** | **Manifest + index step** v1; no chunk column |
| MRC-Q3 | Store `embedding_dimensions`? | **locked** | **Yes** — required when Matryoshka model changes |
| MRC-Q4 | Pipeline-run `models_snapshot` JSONB? | **locked** | **Yes** — denormalized at finalize from steps/attempts |
| MRC-Q5 | Relation to pipeline observability? | **locked** | **Sibling** — MRC owns model identity; PO owns tokens/latency/failures; share `github_llm_call_attempts` |
| MRC-Q6 | Manual index without pipeline run? | **locked** | **Defer** attempt rows; optional index-job-only log field later |
| MRC-Q7 | Retrieve query embed model? | **open** (lean **manifest v1.1**) | Record when `search_revision_chunks` runs in review path |
| MRC-Q8 | `embed_batches=0` (full chunk reuse)? | **locked** | Omit `embedding_*` keys or set `embedding_model: null` with `embedding_skipped_reason=reused_chunks_only` — **never** current env model |
| MRC-Q9 | `models_snapshot` writer? | **locked** | **Terminal write** after publish complete (or pipeline failure terminal hook); not incremental per stage in v1 |
| MRC-Q10 | PO vs MRC Voyage attempt owner? | **locked** | **PO-P1.4** wires recorder; **MRC-P1** verifies `request_model` + judge/publish step gaps |

---

## Parking lot

- API/UI: show `models_snapshot` on pipeline trace response (MRC-P3).
- Alert when retrieve query model ≠ index manifest embedding model (cross-model search bug).
- Bedrock paths when `REVY_*_PROVIDER=bedrock` enabled.

---

## Devil's advocate

- **Manifest-only is enough** — if PO attempt rows ship with `request_model`, snapshot may be redundant; counter: manifest survives even if attempt recorder fails mid-batch.
- **Over-storing** — model ids change strings often; counter: that's exactly why we capture per run.

---

## References

- `backend/app/services/github_pipeline_trace.py` — `record_index_pipeline_step` (no model today)
- `backend/app/integrations/voyage_embeddings.py` — no recorder
- `backend/app/services/github_review.py` — reviewer `model_id` + `start_attempt`
- `backend/app/models/github_llm_call_attempt.py` — `request_model`, `step_type=index_embed`
- `backend/scripts/pipeline_observability_staging_metrics.py` — no model breakdown
- `docs/models/voyage-embeddings/VOYAGE_CODE_4_FINDINGS.md`
